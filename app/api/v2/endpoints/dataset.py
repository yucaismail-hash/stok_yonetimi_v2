# app/api/v2/endpoints/dataset.py
"""
Dataset API Endpoints
DOCUMENT 02 - Dataset Lifecycle
"""

from typing import Optional, Dict, Any, List
import hashlib
import json
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, UploadFile, File, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user
from app.models.company import User
from app.models.dataset import (
    Dataset, 
    DatasetState, 
    DatasetOperationType,
    DatasetVersion,
)
from app.schemas.dataset import (
    DatasetCreate,
    DatasetResponse,
    DatasetListResponse,
    DatasetValidateResponse,
    DatasetApproveResponse,
    DatasetVersionResponse,
    DatasetDiffResponse,
)

# Dataset Services
from app.services.dataset import (
    DatasetService,
    DatasetValidationEngine,
    DatasetDiffEngine,
    DatasetVersionService,
    DatasetCacheService,
)
from app.services.security import EncryptionService

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================
# 1. UPLOAD - Veri Yükleme
# ============================================

@router.post(
    "/upload",
    response_model=DatasetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload dataset",
    description="Upload new dataset or append/revision/replacement"
)
async def upload_dataset(
    file: UploadFile = File(...),
    operation_type: str = Form("append"),
    source_type: str = Form("excel"),
    source_name: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Dataset yükleme endpoint'i.
    
    - append: Yeni veri ekleme (mevcut veri korunur)
    - revision: Tarihsel verileri düzeltme (diff gerektirir)
    - replacement: Tam veri değişimi (sadece admin)
    """
    
    # 1. Operation type kontrolü
    try:
        op_type = DatasetOperationType(operation_type.lower())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid operation_type. Must be one of: append, revision, replacement"
        )
    
    # 2. Source type kontrolü
    if source_type not in ["excel", "csv", "rest", "erp"]:
        raise HTTPException(
            status_code=400,
            detail="source_type must be one of: excel, csv, rest, erp"
        )
    
    # 3. Dosya okuma
    try:
        file_content = await file.read()
        file_size = len(file_content)
        
        # Dosya hash'i hesapla
        file_hash = hashlib.sha256(file_content).hexdigest()
        
        # Excel/CSV parse (basit implementasyon - gerçekte excel_reader kullanılacak)
        # Burada örnek veri oluşturuyoruz, gerçekte ExcelReader ile parse edilecek
        data = {
            "items": [
                {"sku_code": "SKU001", "sku_name": "Ürün 1", "week_start": "2026-W01", "demand": 100},
                {"sku_code": "SKU001", "sku_name": "Ürün 1", "week_start": "2026-W02", "demand": 120},
                {"sku_code": "SKU002", "sku_name": "Ürün 2", "week_start": "2026-W01", "demand": 50},
                {"sku_code": "SKU002", "sku_name": "Ürün 2", "week_start": "2026-W02", "demand": 60},
                {"sku_code": "SKU003", "sku_name": "Ürün 3", "week_start": "2026-W01", "demand": 200},
                {"sku_code": "SKU003", "sku_name": "Ürün 3", "week_start": "2026-W02", "demand": 180},
            ]
        }
        
        # SKU ve record sayıları
        skus = set(item.get("sku_code") for item in data["items"] if item.get("sku_code"))
        sku_count = len(skus)
        record_count = len(data["items"])
        
        # Tarih aralığı
        weeks = [item.get("week_start") for item in data["items"] if item.get("week_start")]
        date_range_start = min(weeks) if weeks else None
        date_range_end = max(weeks) if weeks else None
        
        # Dataset hash
        dataset_hash = hashlib.sha256(
            json.dumps(data, sort_keys=True).encode()
        ).hexdigest()
        
        # 4. Dataset'i oluştur
        dataset = Dataset(
            user_id=current_user.id,
            dataset_hash=dataset_hash,
            dataset_version=1,
            source_type=source_type,
            source_name=source_name or file.filename,
            state=DatasetState.UPLOADED.value,
            operation_type=op_type.value,
            uploaded_by=current_user.id,
            upload_timestamp=datetime.now(),
            record_count=record_count,
            sku_count=sku_count,
            date_range_start=date_range_start,
            date_range_end=date_range_end,
            is_active=True,
        )
        
        # 5. Encryption - DOCUMENT 02 Section 15
        encryption = EncryptionService(db)
        encrypted_data = encryption.encrypt_dataset(current_user.id, data)
        dataset.encrypted_data = encrypted_data
        
        db.add(dataset)
        db.commit()
        db.refresh(dataset)
        
        # 6. Log event - DOCUMENT 02 Section 17
        version_service = DatasetVersionService(db)
        version_service.log_event(
            dataset_id=dataset.id,
            event_type="uploaded",
            user_id=current_user.id,
            event_data={"filename": file.filename, "operation_type": op_type.value}
        )
        
        logger.info(f"✅ Dataset uploaded: {dataset.id} by user {current_user.id}")
        
        return DatasetResponse(
            id=dataset.id,
            user_id=dataset.user_id,
            dataset_hash=dataset.dataset_hash,
            dataset_version=dataset.dataset_version,
            source_type=dataset.source_type,
            source_name=dataset.source_name,
            state=dataset.state,
            operation_type=dataset.operation_type,
            record_count=dataset.record_count,
            sku_count=dataset.sku_count,
            date_range_start=dataset.date_range_start,
            date_range_end=dataset.date_range_end,
            created_at=dataset.created_at,
            is_active=dataset.is_active,
            status_message="Dataset uploaded successfully. Validation required."
        )
        
    except Exception as e:
        logger.error(f"❌ Upload error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )


# ============================================
# 2. VALIDATE - Validasyon Çalıştırma
# ============================================

@router.post(
    "/validate/{dataset_id}",
    response_model=DatasetValidateResponse,
    summary="Validate dataset",
    description="Run validation wizard on dataset"
)
async def validate_dataset(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Dataset validasyon endpoint'i.
    DOCUMENT 02 - Section 12: Validation Wizard
    """
    
    # 1. Dataset'i kontrol et
    dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id,
        Dataset.user_id == current_user.id,
        Dataset.is_active == True
    ).first()
    
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )
    
    # 2. Dataset'i decrypt et
    try:
        encryption = EncryptionService(db)
        data = encryption.decrypt_dataset(current_user.id, dataset.encrypted_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Decryption failed: {str(e)}"
        )
    
    # 3. Validation çalıştır
    validation_engine = DatasetValidationEngine(db)
    validation_result = validation_engine.validate(dataset, data)
    
    # 4. Dataset state'ini güncelle
    if validation_result.is_valid:
        dataset.state = DatasetState.VALIDATED.value
        db.add(dataset)
        db.commit()
        
        # 5. Log event
        version_service = DatasetVersionService(db)
        version_service.log_event(
            dataset_id=dataset.id,
            event_type="validated",
            user_id=current_user.id,
            event_data={"is_valid": True, "warnings_count": len(validation_result.warnings)}
        )
    
    return DatasetValidateResponse(
        dataset_id=dataset.id,
        is_valid=validation_result.is_valid,
        errors=validation_result.errors or [],
        warnings=validation_result.warnings or [],
        requires_approval=validation_result.requires_user_approval,
        status="validated" if validation_result.is_valid else "failed",
        message="Validation completed successfully" if validation_result.is_valid else "Validation failed"
    )


# ============================================
# 3. APPROVE - Onaylama
# ============================================

@router.post(
    "/approve/{dataset_id}",
    response_model=DatasetApproveResponse,
    summary="Approve dataset",
    description="Approve dataset after validation"
)
async def approve_dataset(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Dataset onay endpoint'i.
    DOCUMENT 02 - Section 13: Change Validation
    """
    
    # 1. Dataset'i kontrol et
    dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id,
        Dataset.user_id == current_user.id,
        Dataset.is_active == True
    ).first()
    
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )
    
    # 2. State kontrolü
    if dataset.state != DatasetState.VALIDATED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot approve dataset in state: {dataset.state}. Must be in 'validated' state."
        )
    
    # 3. Dataset'i decrypt et
    try:
        encryption = EncryptionService(db)
        data = encryption.decrypt_dataset(current_user.id, dataset.encrypted_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Decryption failed: {str(e)}"
        )
    
    # 4. Diff çalıştır (DOCUMENT 02 - Section 11)
    diff_engine = DatasetDiffEngine(db)
    
    # Önceki dataset'i bul
    previous_dataset = db.query(Dataset).filter(
        Dataset.user_id == current_user.id,
        Dataset.state == DatasetState.APPROVED.value,
        Dataset.is_active == True,
        Dataset.id != dataset.id
    ).order_by(Dataset.id.desc()).first()
    
    old_data = None
    if previous_dataset and previous_dataset.encrypted_data:
        try:
            old_data = encryption.decrypt_dataset(current_user.id, previous_dataset.encrypted_data)
        except:
            pass
    
    diff_result = diff_engine.diff(data, old_data)
    diff_result["previous_dataset_id"] = previous_dataset.id if previous_dataset else None
    
    # 5. Diff kaydet
    diff_record = diff_engine.save_diff_result(dataset.id, diff_result)
    
    # 6. Versiyon oluştur (DOCUMENT 02 - Section 7)
    version_service = DatasetVersionService(db)
    version = version_service.create_version(dataset.id, current_user.id)
    
    # 7. Dataset state'ini güncelle
    dataset.state = DatasetState.APPROVED.value
    db.add(dataset)
    db.commit()
    
    # 8. Log event
    version_service.log_event(
        dataset_id=dataset.id,
        event_type="approved",
        user_id=current_user.id,
        event_data={
            "version": version.version_number,
            "diff": {
                "new_skus": len(diff_result.get("new_skus", [])),
                "removed_skus": len(diff_result.get("removed_skus", [])),
                "modified_skus": len(diff_result.get("modified_skus", []))
            }
        }
    )
    
    return DatasetApproveResponse(
        dataset_id=dataset.id,
        version=version.version_number,
        status="approved",
        message=f"Dataset approved successfully. Version {version.version_number} created.",
        diff_summary={
            "new_skus": len(diff_result.get("new_skus", [])),
            "removed_skus": len(diff_result.get("removed_skus", [])),
            "modified_skus": len(diff_result.get("modified_skus", [])),
            "requires_approval": diff_record.requires_approval
        }
    )


# ============================================
# 4. GET - Dataset Getir
# ============================================

@router.get(
    "/{dataset_id}",
    response_model=DatasetResponse,
    summary="Get dataset",
    description="Get dataset by ID (decrypted in memory)"
)
async def get_dataset(
    dataset_id: int,
    include_data: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Dataset bilgilerini getir.
    """
    
    dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id,
        Dataset.user_id == current_user.id
    ).first()
    
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )
    
    response = DatasetResponse(
        id=dataset.id,
        user_id=dataset.user_id,
        dataset_hash=dataset.dataset_hash,
        dataset_version=dataset.dataset_version,
        source_type=dataset.source_type,
        source_name=dataset.source_name,
        state=dataset.state,
        operation_type=dataset.operation_type,
        record_count=dataset.record_count,
        sku_count=dataset.sku_count,
        date_range_start=dataset.date_range_start,
        date_range_end=dataset.date_range_end,
        created_at=dataset.created_at,
        updated_at=dataset.updated_at,
        expires_at=dataset.expires_at,
        is_active=dataset.is_active,
    )
    
    # Veriyi de döndür (sadece memory'de decrypt)
    if include_data and dataset.encrypted_data:
        try:
            encryption = EncryptionService(db)
            data = encryption.decrypt_dataset(current_user.id, dataset.encrypted_data)
            response.data = data
        except Exception as e:
            response.status_message = f"Decryption failed: {str(e)}"
    
    return response


# ============================================
# 5. VERSIONS - Versiyon Geçmişi
# ============================================

@router.get(
    "/{dataset_id}/versions",
    response_model=List[DatasetVersionResponse],
    summary="Get dataset versions",
    description="Get all versions of a dataset"
)
async def get_dataset_versions(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Dataset'in tüm versiyonlarını getir.
    """
    
    # Dataset kontrolü
    dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id,
        Dataset.user_id == current_user.id
    ).first()
    
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )
    
    version_service = DatasetVersionService(db)
    versions = version_service.get_all_versions(dataset_id)
    
    return [
        DatasetVersionResponse(
            id=v.id,
            dataset_id=v.dataset_id,
            version_number=v.version_number,
            dataset_hash=v.dataset_hash,
            record_count=v.record_count,
            sku_count=v.sku_count,
            created_by=v.created_by,
            created_at=v.created_at,
            is_current=v.is_current,
            is_archived=v.is_archived,
        )
        for v in versions
    ]


# ============================================
# 6. DIFF - Diff Sonucu Getir
# ============================================

@router.get(
    "/{dataset_id}/diff",
    response_model=DatasetDiffResponse,
    summary="Get dataset diff",
    description="Get diff result of dataset"
)
async def get_dataset_diff(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Dataset'in diff sonucunu getir.
    """
    
    dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id,
        Dataset.user_id == current_user.id
    ).first()
    
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )
    
    diff_result = db.query(DatasetDiffResult).filter(
        DatasetDiffResult.dataset_id == dataset_id
    ).first()
    
    if not diff_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diff result not found"
        )
    
    return DatasetDiffResponse(
        dataset_id=diff_result.dataset_id,
        previous_dataset_id=diff_result.previous_dataset_id,
        new_skus=diff_result.new_skus or [],
        removed_skus=diff_result.removed_skus or [],
        modified_skus=diff_result.modified_skus or [],
        modified_historical_values=diff_result.modified_historical_values or [],
        missing_periods=diff_result.missing_periods or [],
        duplicate_records=diff_result.duplicate_records or [],
        total_changes=diff_result.total_changes,
        requires_approval=diff_result.requires_approval,
        executed_at=diff_result.executed_at,
    )


# ============================================
# 7. LIST - Dataset Listele
# ============================================

@router.get(
    "/",
    response_model=DatasetListResponse,
    summary="List datasets",
    description="List all datasets for current user"
)
async def list_datasets(
    skip: int = 0,
    limit: int = 50,
    state: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Dataset listesini getir.
    """
    
    query = db.query(Dataset).filter(
        Dataset.user_id == current_user.id,
        Dataset.is_active == True
    )
    
    if state:
        query = query.filter(Dataset.state == state)
    
    total = query.count()
    datasets = query.order_by(Dataset.created_at.desc()).offset(skip).limit(limit).all()
    
    return DatasetListResponse(
        total=total,
        skip=skip,
        limit=limit,
        items=[
            DatasetResponse(
                id=d.id,
                user_id=d.user_id,
                dataset_hash=d.dataset_hash,
                dataset_version=d.dataset_version,
                source_type=d.source_type,
                source_name=d.source_name,
                state=d.state,
                operation_type=d.operation_type,
                record_count=d.record_count,
                sku_count=d.sku_count,
                date_range_start=d.date_range_start,
                date_range_end=d.date_range_end,
                created_at=d.created_at,
                updated_at=d.updated_at,
                expires_at=d.expires_at,
                is_active=d.is_active,
            )
            for d in datasets
        ]
    )


# ============================================
# 8. REVISION - Dataset Revize Etme
# ============================================

@router.post(
    "/revision/{dataset_id}",
    response_model=DatasetResponse,
    summary="Create revision",
    description="Create a new revision of existing dataset"
)
async def create_revision(
    dataset_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Mevcut dataset'i revize et.
    DOCUMENT 02 - Section 6: Revision
    """
    
    # Mevcut dataset'i kontrol et
    old_dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id,
        Dataset.user_id == current_user.id,
        Dataset.is_active == True,
        Dataset.state == DatasetState.APPROVED.value
    ).first()
    
    if not old_dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active approved dataset not found"
        )
    
    # Yeni veriyi oku
    try:
        file_content = await file.read()
        
        # Yeni veriyi parse et (örnek)
        new_data = {
            "items": [
                {"sku_code": "SKU001", "sku_name": "Ürün 1", "week_start": "2026-W01", "demand": 100},
                {"sku_code": "SKU001", "sku_name": "Ürün 1", "week_start": "2026-W02", "demand": 120},
                {"sku_code": "SKU002", "sku_name": "Ürün 2", "week_start": "2026-W01", "demand": 50},
                {"sku_code": "SKU002", "sku_name": "Ürün 2", "week_start": "2026-W02", "demand": 60},
                {"sku_code": "SKU003", "sku_name": "Ürün 3", "week_start": "2026-W01", "demand": 200},
                {"sku_code": "SKU003", "sku_name": "Ürün 3", "week_start": "2026-W02", "demand": 180},
                {"sku_code": "SKU001", "sku_name": "Ürün 1", "week_start": "2026-W03", "demand": 110},
                {"sku_code": "SKU002", "sku_name": "Ürün 2", "week_start": "2026-W03", "demand": 55},
            ]
        }
        
        # Revision dataset'i oluştur
        dataset = Dataset(
            user_id=current_user.id,
            dataset_hash=hashlib.sha256(json.dumps(new_data, sort_keys=True).encode()).hexdigest(),
            dataset_version=old_dataset.dataset_version + 1,
            source_type="revision",
            source_name=file.filename,
            state=DatasetState.UPLOADED.value,
            operation_type=DatasetOperationType.REVISION.value,
            uploaded_by=current_user.id,
            upload_timestamp=datetime.now(),
            record_count=len(new_data["items"]),
            sku_count=len(set(item["sku_code"] for item in new_data["items"])),
            previous_version_id=old_dataset.id,
            is_active=True,
        )
        
        # Şifrele
        encryption = EncryptionService(db)
        dataset.encrypted_data = encryption.encrypt_dataset(current_user.id, new_data)
        
        db.add(dataset)
        db.commit()
        db.refresh(dataset)
        
        # Log event
        version_service = DatasetVersionService(db)
        version_service.log_event(
            dataset_id=dataset.id,
            event_type="revision_created",
            user_id=current_user.id,
            event_data={"previous_version": old_dataset.dataset_version}
        )
        
        logger.info(f"✅ Revision created for dataset {old_dataset.id}: {dataset.id}")
        
        return DatasetResponse(
            id=dataset.id,
            user_id=dataset.user_id,
            dataset_hash=dataset.dataset_hash,
            dataset_version=dataset.dataset_version,
            source_type=dataset.source_type,
            source_name=dataset.source_name,
            state=dataset.state,
            operation_type=dataset.operation_type,
            record_count=dataset.record_count,
            sku_count=dataset.sku_count,
            created_at=dataset.created_at,
            is_active=dataset.is_active,
            status_message="Revision uploaded. Validate and approve to complete."
        )
        
    except Exception as e:
        logger.error(f"❌ Revision error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Revision failed: {str(e)}"
        )