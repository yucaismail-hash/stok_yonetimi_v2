"""FU2 staged canonical XLSX ingestion; Excel is never an analytical authority."""
from __future__ import annotations

import hashlib
import io
import json
from datetime import datetime, timezone

from openpyxl import Workbook, load_workbook
from sqlalchemy.orm import Session

from app.application.actual_weekly_ledger import ActualWeeklyLedgerService
from app.models.actuals import ActualWeeklyRevision
from app.models.dataset import Dataset, DatasetEvent, DatasetState, DatasetValidationResult, DatasetVersion
from app.services.dataset.ingestion_policy import validate_demand_type
from app.services.dataset.weekly_normalization import parse_weekly_period
from app.services.security import EncryptionService


SHEET = "Talep_Gecmisi"
REQUIRED = ("Malzeme Kodu", "Talep Tipi", "Ürün Seviyesi", "Dönem", "Miktar")
OPTIONAL = ("Ürün Grubu", "Ürün Sınıfı")
ALIASES = {
    "Malzeme Kodu": {"malzeme kodu", "ürün kodu", "product code", "material code"},
    "Talep Tipi": {"talep tipi", "demand type"},
    "Ürün Seviyesi": {"ürün seviyesi", "product level", "material type"},
    "Dönem": {"dönem", "period", "week"},
    "Miktar": {"miktar", "quantity", "demand"},
    "Ürün Grubu": {"ürün grubu", "product group"},
    "Ürün Sınıfı": {"ürün sınıfı", "product class"},
}
LEVELS = {"finished_good", "semi_finished_good", "raw_material"}


class CanonicalExcelError(ValueError):
    pass


def _norm(value):
    return " ".join(str(value or "").strip().casefold().split())


def template_bytes() -> bytes:
    book = Workbook(); sheet = book.active; sheet.title = SHEET
    sheet.append(list(REQUIRED) + list(OPTIONAL))
    sheet.append(["SKU-001", "sales", "finished_good", "2026-W01", 100, "Örnek Grup", "Örnek Sınıf"])
    sheet.append(["SKU-001", "sales", "finished_good", "2026-W02", 102, "Örnek Grup", "Örnek Sınıf"])
    note = book.create_sheet("Açıklama")
    note.append(["FU2 Pilot Şablonu"])
    note.append(["Zorunlu alanlar", ", ".join(REQUIRED)])
    note.append(["Opsiyonel alanlar", ", ".join(OPTIONAL)])
    note.append(["Talep Tipi", "sales veya consumption"])
    note.append(["Ürün Seviyesi", "finished_good, semi_finished_good veya raw_material"])
    note.append(["Dönem", "ISO hafta: YYYY-Www; örn. 2026-W01"])
    output = io.BytesIO(); book.save(output); return output.getvalue()


def parse_workbook(content: bytes):
    try:
        book = load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    except Exception as exc:
        raise CanonicalExcelError("WORKBOOK_UNREADABLE") from exc
    if SHEET not in book.sheetnames:
        return [], [{"code":"REQUIRED_SHEET_MISSING","sheet":SHEET,"row":None,"column":None,"severity":"ERROR","message":"Talep_Gecmisi sayfası bulunamadı."}]
    sheet = book[SHEET]
    rows = list(sheet.iter_rows(values_only=True))
    if not rows:
        return [], [{"code":"SHEET_EMPTY","sheet":SHEET,"row":None,"column":None,"severity":"ERROR","message":"Talep_Gecmisi sayfası boş."}]
    header = list(rows[0]); mapped = {}; errors = []
    for index, value in enumerate(header):
        matches = [canonical for canonical, aliases in ALIASES.items() if _norm(value) in aliases]
        if len(matches) > 1:
            errors.append({"code":"AMBIGUOUS_COLUMN","sheet":SHEET,"row":1,"column":str(value),"severity":"ERROR","message":"Kolon eşlemesi belirsiz."})
        elif matches:
            if matches[0] in mapped:
                errors.append({"code":"AMBIGUOUS_COLUMN","sheet":SHEET,"row":1,"column":str(value),"severity":"ERROR","message":"Aynı kanonik alan iki kolondan geliyor."})
            mapped[matches[0]] = index
    for field in REQUIRED:
        if field not in mapped:
            errors.append({"code":"REQUIRED_COLUMN_MISSING","sheet":SHEET,"row":1,"column":field,"severity":"ERROR","message":f"Zorunlu kolon eksik: {field}."})
    if errors: return [], errors
    parsed = []; identities = set()
    for row_no, values in enumerate(rows[1:], 2):
        if not any(value not in (None, "") for value in values): continue
        def cell(field): return values[mapped[field]] if mapped[field] < len(values) else None
        item = {"material_code": str(cell("Malzeme Kodu") or "").strip(), "demand_type": str(cell("Talep Tipi") or "").strip().lower(), "product_level": str(cell("Ürün Seviyesi") or "").strip().lower(), "period": str(cell("Dönem") or "").strip(), "quantity": cell("Miktar"), "product_group": str(cell("Ürün Grubu") or "").strip() if "Ürün Grubu" in mapped else None, "product_class": str(cell("Ürün Sınıfı") or "").strip() if "Ürün Sınıfı" in mapped else None}
        try:
            if not item["material_code"]: raise CanonicalExcelError("MATERIAL_CODE_REQUIRED")
            item["demand_type"] = validate_demand_type(item["demand_type"])
            if item["demand_type"] not in {"sales", "consumption"}: raise CanonicalExcelError("DEMAND_TYPE_UNSUPPORTED")
            if item["product_level"] not in LEVELS: raise CanonicalExcelError("PRODUCT_LEVEL_UNSUPPORTED")
            item["period"] = parse_weekly_period(item["period"]).period
            if isinstance(item["quantity"], bool) or float(item["quantity"]) < 0: raise CanonicalExcelError("QUANTITY_INVALID")
            item["quantity"] = float(item["quantity"])
            identity = (item["material_code"], item["demand_type"], item["period"])
            if identity in identities: raise CanonicalExcelError("DUPLICATE_ROW_IDENTITY")
            identities.add(identity); parsed.append(item)
        except (ValueError, TypeError, CanonicalExcelError) as exc:
            raw_code = str(exc)
            code = {
                "invalid demand_type": "DEMAND_TYPE_UNSUPPORTED",
                "weekly period must use YYYY-Www": "PERIOD_INVALID",
                "invalid ISO weekly period": "PERIOD_INVALID",
            }.get(raw_code, raw_code)
            errors.append({"code":code,"sheet":SHEET,"row":row_no,"column":None,"severity":"ERROR","message":"Geçersiz satır; malzeme, talep tipi, ürün seviyesi, dönem ve miktarı kontrol edin."})
    if not parsed and not errors:
        errors.append({"code":"SHEET_EMPTY","sheet":SHEET,"row":None,"column":None,"severity":"ERROR","message":"Talep_Gecmisi sayfasında veri yok."})
    return parsed, errors


class CanonicalExcelIngestionService:
    def get_current_accepted(self, session: Session, company_id):
        """Return the tenant's most recently accepted active dataset deterministically."""
        row = (
            session.query(Dataset, DatasetEvent)
            .join(
                DatasetEvent,
                (DatasetEvent.dataset_id == Dataset.id) & (DatasetEvent.event_type == "accepted"),
            )
            .filter(
                Dataset.company_id == company_id,
                Dataset.is_active.is_(True),
                Dataset.is_deleted.is_(False),
                Dataset.state == DatasetState.APPROVED,
                DatasetEvent.is_deleted.is_(False),
            )
            .order_by(DatasetEvent.created_at.desc(), DatasetEvent.id.desc())
            .first()
        )
        if row is None:
            return None
        dataset, accepted_event = row
        return {
            "dataset_id": str(dataset.id),
            "status": "READY_FOR_WORKFLOW",
            "accepted": True,
            "accepted_at": accepted_event.created_at,
            "created_at": dataset.created_at,
            "source_name": dataset.source_name,
            "record_count": dataset.record_count,
            "material_count": dataset.sku_count,
        }

    def stage(self, session: Session, company_id, user_id, filename: str, content: bytes):
        if not filename.lower().endswith(".xlsx"):
            raise CanonicalExcelError("FILE_TYPE_INVALID")
        rows, errors = parse_workbook(content)
        fingerprint = hashlib.sha256(str(company_id).encode() + content).hexdigest()
        existing = session.query(Dataset).filter_by(company_id=company_id, dataset_hash=fingerprint, is_active=True).one_or_none()
        if existing:
            return existing, True
        periods = [item["period"] for item in rows]
        dataset = Dataset(company_id=company_id, user_id=user_id, uploaded_by=user_id, dataset_hash=fingerprint, source_type="excel", source_name=filename, state=DatasetState.VALIDATED if not errors else DatasetState.FAILED, record_count=len(rows), sku_count=len({item["material_code"] for item in rows}), encrypted_data=EncryptionService(session).encrypt_dataset(user_id, {"actual_rows": rows, "contract":"fu2_weekly_v1"}), is_active=True)
        session.add(dataset); session.flush()
        session.add(DatasetValidationResult(dataset_id=dataset.id, is_valid=not errors, errors=errors, warnings=[], validated_by=user_id, requires_user_approval=not errors))
        session.add(DatasetEvent(dataset_id=dataset.id, event_type="validated" if not errors else "validation_failed", event_data={"periods": sorted(periods), "contract":"fu2_weekly_v1"}, created_by=user_id))
        session.commit(); return dataset, False

    def accept(self, session: Session, company_id, user_id, dataset_id):
        dataset = session.query(Dataset).filter_by(id=dataset_id, company_id=company_id, user_id=user_id, is_active=True).one_or_none()
        if not dataset: raise CanonicalExcelError("DATASET_UNAVAILABLE")
        if dataset.state == DatasetState.APPROVED: return {"status":"READY_FOR_WORKFLOW","dataset_id":str(dataset.id),"idempotent":True}
        validation = session.query(DatasetValidationResult).filter_by(dataset_id=dataset.id).order_by(DatasetValidationResult.validated_at.desc()).first()
        if not validation or not validation.is_valid: raise CanonicalExcelError("DATASET_NOT_READY_FOR_ACCEPTANCE")
        payload = EncryptionService(session).decrypt_dataset(user_id, dataset.encrypted_data)
        version = DatasetVersion(dataset_id=dataset.id, version_number=1, dataset_hash=dataset.dataset_hash, record_count=dataset.record_count, sku_count=dataset.sku_count, created_by=user_id, is_current=True)
        session.add(version); session.flush(); session.commit()
        grouped = {}
        for row in payload["actual_rows"]: grouped.setdefault(row["demand_type"], []).append(row)
        ledger = ActualWeeklyLedgerService()
        summary = {kind: ledger.ingest_dataset_actuals(company_id, user_id, dataset.id, rows, kind) for kind, rows in grouped.items()}
        # Dataset acceptance is the explicit approval boundary for its staged corrections.
        proposed = session.query(ActualWeeklyRevision).filter_by(company_id=company_id, source_dataset_id=dataset.id, approval_status="proposed").all()
        for revision in proposed:
            ledger.approve_revision(company_id, revision.id, user_id)
        dataset = session.query(Dataset).filter_by(id=dataset.id).one(); dataset.state = DatasetState.APPROVED
        session.add(DatasetEvent(dataset_id=dataset.id, event_type="accepted", event_data={"ledger":summary,"status":"READY_FOR_WORKFLOW"}, created_by=user_id)); session.commit()
        return {"status":"READY_FOR_WORKFLOW","dataset_id":str(dataset.id),"version_id":str(version.id),"ledger":summary,"idempotent":False}
