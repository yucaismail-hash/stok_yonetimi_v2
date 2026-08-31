"""Persisted Dataset provider for the currently wired deterministic capabilities."""
from app.engine.capability_registry import Capability
from app.engine.capability_executor import CapabilityInputValidationError, DatasetInputUnavailableError
from app.models.dataset import Dataset
from app.models.actuals import ActualWeeklyRevision
from app.models.dataset_version_product_input import DatasetVersionProductInput
from app.models.dataset import DatasetEvent, DatasetState, DatasetVersion
from app.services.security import EncryptionService
from app.engine.capability_dataflow import assemble_simulation_business_input, assemble_safety_stock_business_input
from app.services.dataset.weekly_normalization import parse_weekly_period
from app.application.current_incoming_supply import resolve_current_incoming_supply


class DatasetRuntimeProvider:
    def __init__(self, session, encryption_service_factory=EncryptionService):
        self._session = session
        self._encryption_service_factory = encryption_service_factory

    def __call__(self, request):
        if request.capability is Capability.SUPPLIER_ANALYSIS:
            dataset=self._session.query(Dataset).filter_by(id=request.dataset_id,company_id=request.company_id,user_id=request.user_id,is_active=True).one_or_none()
            if not dataset or not dataset.encrypted_data: raise DatasetInputUnavailableError('authorized dataset is unavailable')
            try: payload=self._encryption_service_factory(self._session).decrypt_dataset(request.user_id,dataset.encrypted_data)
            except Exception as exc: raise DatasetInputUnavailableError('dataset payload cannot be loaded') from exc
            status=self.supplier_evidence_status(payload)
            if not status['available']: raise CapabilityInputValidationError(status['reason'])
            suppliers=payload['suppliers']; mappings=payload['supplier_mapping']
            return {'suppliers':suppliers,'supplier_mapping':mappings,'dataset_id':str(dataset.id)}
        if request.capability not in (Capability.DEMAND_FORECAST, Capability.SAFETY_STOCK, Capability.SIMULATION, Capability.BACKTEST):
            raise DatasetInputUnavailableError("capability dataset input is unavailable")
        dataset = self._session.query(Dataset).filter_by(id=request.dataset_id, company_id=request.company_id, user_id=request.user_id, is_active=True).one_or_none()
        if not dataset:
            raise DatasetInputUnavailableError("authorized dataset is unavailable")
        if not dataset.encrypted_data:
            raise CapabilityInputValidationError("dataset payload is unavailable")
        try:
            payload = self._encryption_service_factory(self._session).decrypt_dataset(request.user_id, dataset.encrypted_data)
        except Exception as exc:
            raise DatasetInputUnavailableError("dataset payload cannot be loaded") from exc
        items, configured_service_level = self._runtime_items(dataset, request, payload)
        requested = set(request.material_codes or [])
        selected = []
        found = set()
        for item in items:
            if not isinstance(item, dict):
                continue
            code = item.get("sku_code")
            if not isinstance(code, str) or (requested and code not in requested):
                continue
            history = item.get("demand_history", [])
            if not isinstance(history, list) or len(history) < 4 or not all(isinstance(value, (int, float)) and not isinstance(value, bool) for value in history):
                continue
            prepared = {"material_code": code, "demand_history": list(history)}
            if request.capability is Capability.DEMAND_FORECAST and isinstance(request.params.get('demand_type'),str) and isinstance(request.params.get('forecast_cutoff_period'),str):
                prepared.update({'demand_type':request.params['demand_type'],'forecast_cutoff_period':request.params['forecast_cutoff_period']})
            if request.capability is Capability.SAFETY_STOCK:
                lead_time_days = item.get("lead_time_days")
                if isinstance(lead_time_days, bool) or not isinstance(lead_time_days, (int, float)) or lead_time_days <= 0:
                    raise CapabilityInputValidationError(f"lead_time_days is required and positive for {code}")
                prepared["lead_time_days"] = float(lead_time_days)
                prepared["supplier_enrichment"] = {"status":"unavailable","lead_time_source":"dataset_manual","supplier_result_reference_ids":[]}
            if request.capability is Capability.SIMULATION:
                lead_time_days=item.get('lead_time_days')
                if isinstance(lead_time_days,bool) or not isinstance(lead_time_days,(int,float)) or lead_time_days<=0: raise CapabilityInputValidationError(f'lead_time_days is required and positive for {code}')
                prepared.update({'lead_time_days':float(lead_time_days),'initial_stock':item.get('initial_stock'),'eoq':item.get('eoq'),'existing_rop':item.get('rop'),'existing_safety_stock':item.get('safety_stock'),'incoming_supply':item.get('incoming_supply')})
            if request.capability is Capability.BACKTEST:
                lead=item.get('lead_time_days')
                if isinstance(lead,bool) or not isinstance(lead,(int,float)) or lead<=0: raise CapabilityInputValidationError(f'lead_time_days is required and positive for {code}')
                prepared['lead_time_days']=float(lead)
            selected.append(prepared)
            found.add(code)
        missing = sorted(requested - found)
        if missing:
            raise CapabilityInputValidationError("requested material codes are unavailable")
        if not selected:
            raise CapabilityInputValidationError("no capability-ready demand history is available")
        if request.capability is Capability.SAFETY_STOCK and request.upstream_results.get('supplier'):
            return assemble_safety_stock_business_input({'items':selected},request.upstream_results['supplier'])
        if request.capability is Capability.SIMULATION and request.upstream_results:
            policies = {
                item["material_code"]: {
                    "initial_stock": item["initial_stock"],
                    "eoq": item["eoq"],
                }
                for item in selected
            }
            return assemble_simulation_business_input({"policies": policies}, request.upstream_results)
        return {"items": selected, "warnings": [], "dataset_id": str(dataset.id), "service_level": configured_service_level}

    def _runtime_items(self, dataset, request, payload):
        """Resolve V3 only from accepted versioned state; legacy payload is isolated fallback."""
        if isinstance(payload, dict) and payload.get("contract") == "official_v3":
            return self._official_v3_items(dataset, request, payload), payload.get("service_level", {"mode": "automatic"})
        # Legacy pilot datasets predate DatasetVersionProductInput. Remove this fallback only when they are retired.
        return (payload.get("items", []) if isinstance(payload, dict) else []), {"mode": "automatic"}

    def preflight(self, request):
        """Return canonical persisted evidence for readiness checks; never writes or invokes analytics."""
        if request.capability not in (Capability.DEMAND_FORECAST, Capability.SAFETY_STOCK, Capability.SIMULATION, Capability.BACKTEST):
            raise DatasetInputUnavailableError("capability dataset input is unavailable")
        dataset = self._session.query(Dataset).filter_by(id=request.dataset_id, company_id=request.company_id, user_id=request.user_id, is_active=True).one_or_none()
        if not dataset or not dataset.encrypted_data:
            raise DatasetInputUnavailableError("authorized dataset is unavailable")
        try:
            payload = self._encryption_service_factory(self._session).decrypt_dataset(request.user_id, dataset.encrypted_data)
        except Exception as exc:
            raise DatasetInputUnavailableError("dataset payload cannot be loaded") from exc
        items, configured_service_level = self._runtime_items(dataset, request, payload)
        latest_count = sum(item.get("scope_source") == "LATEST_UPLOAD" for item in items if isinstance(item, dict))
        absent_count = sum(item.get("scope_source") == "ALL_ACTIVE_SKUS" for item in items if isinstance(item, dict))
        stale_master_count = sum(
            "EFFECTIVE_MASTER_FROM_PRIOR_UPLOAD" in item.get("temporal_warnings", [])
            for item in items if isinstance(item, dict)
        )
        return {
            "items": items, "supplier": self.supplier_evidence_status(payload, require_dataset_materials=True),
            "dataset_id": str(dataset.id), "service_level": configured_service_level,
            "scope": {"scope_mode": request.params.get("scope_mode", "LATEST_UPLOAD"), "total_selected_count": len(items),
                      "latest_upload_count": latest_count, "absent_from_latest_upload_count": absent_count,
                      "current_snapshot_warning_count": absent_count,
                      "stale_master_warning_count": stale_master_count},
        }

    def _official_v3_items(self, dataset, request, payload):
        if dataset.state != DatasetState.APPROVED:
            raise DatasetInputUnavailableError("official V3 dataset is not accepted")
        version = self._session.query(DatasetVersion).filter_by(dataset_id=dataset.id, is_current=True).one_or_none()
        accepted = self._session.query(DatasetEvent).filter_by(dataset_id=dataset.id, event_type="accepted").order_by(DatasetEvent.created_at.desc(), DatasetEvent.id.desc()).first()
        if version is None or accepted is None:
            raise DatasetInputUnavailableError("official V3 accepted dataset version is unavailable")
        demand_type = payload.get("demand_type")
        if not isinstance(demand_type, str):
            raise DatasetInputUnavailableError("official V3 demand type is unavailable")
        inputs = self._session.query(DatasetVersionProductInput).filter_by(company_id=request.company_id, dataset_version_id=version.id, is_deleted=False).order_by(DatasetVersionProductInput.material_code).all()
        if not inputs:
            raise DatasetInputUnavailableError("official V3 operational inputs are unavailable")
        revisions = self._session.query(ActualWeeklyRevision).filter(
            ActualWeeklyRevision.company_id == request.company_id,
            ActualWeeklyRevision.demand_type == demand_type,
            ActualWeeklyRevision.approval_status == "accepted",
            # Both timestamps are database-owned, avoiding application/database clock skew.
            ActualWeeklyRevision.created_at <= accepted.created_at,
            ActualWeeklyRevision.is_deleted.is_(False),
        ).order_by(ActualWeeklyRevision.material_code, ActualWeeklyRevision.period, ActualWeeklyRevision.created_at.desc(), ActualWeeklyRevision.id.desc()).all()
        latest = {}
        for revision in revisions:
            latest.setdefault((revision.material_code, revision.period), revision)
        histories = {}
        for (material_code, period), revision in latest.items():
            histories.setdefault(material_code, []).append((parse_weekly_period(period), float(revision.proposed_quantity)))
        scope_mode = request.params.get("scope_mode", "LATEST_UPLOAD")
        if scope_mode not in {"LATEST_UPLOAD", "ALL_ACTIVE_SKUS"}:
            raise DatasetInputUnavailableError("unsupported Business Workflow scope mode")
        latest_inputs = {product.material_code: product for product in inputs}
        # Immutable version inputs are the effective-master source.  Read the
        # accepted lineage even for LATEST_UPLOAD: an empty optional master cell
        # means "not updated", not a destructive clear of a prior valid value.
        prior = self._session.query(DatasetVersionProductInput, DatasetEvent).join(
                DatasetVersion, DatasetVersionProductInput.dataset_version_id == DatasetVersion.id
            ).join(Dataset, DatasetVersion.dataset_id == Dataset.id).join(
                DatasetEvent, DatasetEvent.dataset_id == Dataset.id
            ).filter(
                DatasetVersionProductInput.company_id == request.company_id,
                DatasetVersionProductInput.is_deleted.is_(False), Dataset.state == DatasetState.APPROVED,
                DatasetEvent.event_type == "accepted", DatasetEvent.created_at <= accepted.created_at,
            ).order_by(DatasetEvent.created_at.desc(), DatasetEvent.id.desc(), DatasetVersionProductInput.id.desc()).all()
        lineage_by_material = {}
        for product, _event in prior:
            lineage_by_material.setdefault(product.material_code, []).append(product)
        effective_inputs = latest_inputs if scope_mode == "LATEST_UPLOAD" else {
            material_code: lineage[0] for material_code, lineage in lineage_by_material.items()
        }
        items = []
        for material_code, product in sorted(effective_inputs.items()):
            is_current = material_code in latest_inputs
            master, master_from_prior = self._effective_master_values(
                product, lineage_by_material.get(material_code, [product])
            )
            ordered_history = sorted(histories.get(product.material_code, []), key=lambda row: (row[0].year, row[0].week))
            values = [quantity for _, quantity in ordered_history]
            temporal_warnings = []
            if not is_current:
                # Current operational state is explicitly not inherited.
                temporal_warnings.append("CURRENT_SNAPSHOT_UNAVAILABLE")
            if master_from_prior:
                temporal_warnings.append("EFFECTIVE_MASTER_FROM_PRIOR_UPLOAD")
            requested_weeks = request.params.get("weeks", 26)
            requested_weeks = requested_weeks if isinstance(requested_weeks, int) and not isinstance(requested_weeks, bool) and requested_weeks > 0 else 26
            # A delivery cannot suppress a reorder outside either the actual
            # replenishment lead-time window or the simulation horizon.
            incoming_horizon_days = min(float(master["lead_time_days"]), requested_weeks * 7)
            incoming_supply = resolve_current_incoming_supply(
                payload.get("v3_supplier_inputs"), material_code,
                current_material_available=is_current,
                snapshot_as_of=accepted.created_at.date(),
                replenishment_horizon_days=incoming_horizon_days,
            )
            incoming_supply["replenishment_horizon_days"] = incoming_horizon_days
            temporal_warnings.extend(incoming_supply["warnings"])
            items.append({
                "sku_code": product.material_code,
                "demand_history": values,
                # Readiness needs explainable, persisted evidence boundaries.  The
                # periods are derived from the same accepted revision set as values.
                "history_periods": [period.period for period, _ in ordered_history],
                "lead_time_days": float(master["lead_time_days"]),
                "initial_stock": float(product.initial_stock) if is_current else None,
                "eoq": float(master["lot_size"]),
                "product_level": master["product_level"],
                "product_group": master["product_group"],
                "product_class": master["product_class"],
                "unit_cost": float(master["unit_cost"]) if master["unit_cost"] is not None else None,
                "holding_rate": float(master["holding_rate"]) if master["holding_rate"] is not None else None,
                "stockout_cost": float(master["stockout_cost"]) if master["stockout_cost"] is not None else None,
                "demand_type": demand_type,
                "dataset_version_id": str(version.id),
                "scope_source": "LATEST_UPLOAD" if is_current else "ALL_ACTIVE_SKUS",
                "current_snapshot_available": is_current,
                "temporal_warnings": temporal_warnings,
                "incoming_supply": incoming_supply,
            })
        return items

    @staticmethod
    def _effective_master_values(product, lineage):
        """Preserve the last accepted non-empty effective-master value only.

        `initial_stock` deliberately does not belong here: it is a current
        period snapshot and is handled by the selected workflow scope above.
        """
        fields = (
            "lead_time_days", "lot_size", "unit_cost", "holding_rate", "stockout_cost",
            "product_level", "product_group", "product_class",
        )
        values, inherited = {}, False
        for field in fields:
            value = getattr(product, field)
            if value is None or (isinstance(value, str) and not value.strip()):
                for previous in lineage[1:]:
                    candidate = getattr(previous, field)
                    if candidate is not None and (not isinstance(candidate, str) or candidate.strip()):
                        value, inherited = candidate, True
                        break
            values[field] = value
        return values, inherited

    @staticmethod
    def supplier_evidence_status(payload, require_dataset_materials=False):
        """Classify optional Supplier evidence without fabricating enrichment."""
        if not isinstance(payload, dict): return {'available':False, 'status':'absent', 'reason':'supplier data is absent'}
        suppliers, mappings = payload.get('suppliers'), payload.get('supplier_mapping')
        if suppliers is None and mappings is None: return {'available':False, 'status':'absent', 'reason':'supplier data is absent'}
        if not isinstance(suppliers, dict) or not isinstance(mappings, dict) or not suppliers or not mappings:
            return {'available':False, 'status':'invalid', 'reason':'supplier identities and material mappings are required'}
        materials = {item.get('sku_code') for item in payload.get('items', []) if isinstance(item, dict) and isinstance(item.get('sku_code'), str)}
        for material, mapping in mappings.items():
            entries=mapping if isinstance(mapping,list) else [mapping]
            if not isinstance(material, str) or not entries or any(not isinstance(entry,dict) or entry.get('supplier_id') not in suppliers for entry in entries):
                return {'available':False, 'status':'invalid', 'reason':'supplier mapping is invalid'}
            if require_dataset_materials and material not in materials:
                return {'available':False, 'status':'invalid', 'reason':'supplier mapping material is unavailable in dataset'}
        for info in suppliers.values():
            if not isinstance(info, dict) or not isinstance(info.get('delivery_records'), list) or not info['delivery_records']:
                return {'available':False, 'status':'invalid', 'reason':'supplier delivery evidence is required'}
        return {'available':True, 'status':'available', 'reason':None}
