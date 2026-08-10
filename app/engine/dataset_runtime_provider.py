"""Persisted Dataset provider for the currently wired deterministic capabilities."""
from app.engine.capability_registry import Capability
from app.engine.capability_executor import CapabilityInputValidationError, DatasetInputUnavailableError
from app.models.dataset import Dataset
from app.services.security import EncryptionService
from app.engine.capability_dataflow import assemble_simulation_business_input, assemble_safety_stock_business_input


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
        items = payload.get("items", []) if isinstance(payload, dict) else []
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
            if request.capability is Capability.SAFETY_STOCK:
                lead_time_days = item.get("lead_time_days")
                if isinstance(lead_time_days, bool) or not isinstance(lead_time_days, (int, float)) or lead_time_days <= 0:
                    raise CapabilityInputValidationError(f"lead_time_days is required and positive for {code}")
                prepared["lead_time_days"] = float(lead_time_days)
                prepared["supplier_enrichment"] = {"status":"unavailable","lead_time_source":"dataset_manual","supplier_result_reference_ids":[]}
            if request.capability is Capability.SIMULATION:
                lead_time_days=item.get('lead_time_days')
                if isinstance(lead_time_days,bool) or not isinstance(lead_time_days,(int,float)) or lead_time_days<=0: raise CapabilityInputValidationError(f'lead_time_days is required and positive for {code}')
                prepared.update({'lead_time_days':float(lead_time_days),'initial_stock':item.get('initial_stock'),'eoq':item.get('eoq'),'existing_rop':item.get('rop'),'existing_safety_stock':item.get('safety_stock')})
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
        return {"items": selected, "warnings": [], "dataset_id": str(dataset.id)}

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
