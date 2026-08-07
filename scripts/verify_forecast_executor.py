"""Development-only FAST1 encrypted Dataset → CapabilityExecutor forecast proof."""
import asyncio, hashlib, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from uuid_extensions import uuid7
from app.database import SessionLocal
from app.models.company import Company, User
from app.models.dataset import Dataset
from app.models.security import CompanyEncryptionKey
from app.services.security import EncryptionService
from app.engine.capability_contracts import CapabilityExecutionRequest
from app.engine.capability_executor import CapabilityExecutor, CapabilityInputValidationError, DatasetInputUnavailableError
from app.engine.capability_registry import Capability
from app.engine.dataset_runtime_provider import DatasetRuntimeProvider
from app.engine.adapters.forecast_adapter import forecast_adapter
from app.analysis.forecast import DemandForecaster

async def main():
    session=SessionLocal(); probe='phase2d_forecast_'+str(uuid7()).replace('-','')
    try:
        company=Company(id=uuid7(),name=probe,tax_id=probe); user=User(id=uuid7(),company_id=company.id,email=probe+'@example.invalid',hashed_password='probe'); session.add_all((company,user)); session.flush()
        payload={'items':[{'sku_code':'SKU_A','demand_history':[10,11,12,13,14,15,16,17,18,19,20,21]},{'sku_code':'SKU_B','demand_history':[2,9,3,11,4,8,5,12,6,7,9,13]}]}
        encrypted=EncryptionService(session).encrypt_dataset(user.id,payload)
        dataset=Dataset(id=uuid7(),company_id=company.id,user_id=user.id,uploaded_by=user.id,dataset_hash=hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest(),source_type=probe,encrypted_data=encrypted,is_active=True); session.add(dataset); session.commit()
        request=CapabilityExecutionRequest(uuid7(),'forecast_probe','forecast',Capability.DEMAND_FORECAST,company.id,user.id,dataset.id,30,params={'horizon':4})
        provider=DatasetRuntimeProvider(session); executor=CapabilityExecutor(lambda capability: DemandForecaster if capability is Capability.DEMAND_FORECAST else None,provider,forecast_adapter,lambda invoke,timeout:invoke())
        result=await executor.execute(request); assert result.state.value=='completed' and len(result.result['items'])==2 and all(len(item['forecast'])==4 and item['model_used'] for item in result.result['items'])
        filtered=provider(CapabilityExecutionRequest(uuid7(),'forecast_probe','forecast',Capability.DEMAND_FORECAST,company.id,user.id,dataset.id,30,material_codes=['SKU_A']))
        assert len(filtered['items'])==1
        for bad in (CapabilityExecutionRequest(uuid7(),'w','forecast',Capability.DEMAND_FORECAST,uuid7(),user.id,dataset.id,30),CapabilityExecutionRequest(uuid7(),'w','forecast',Capability.DEMAND_FORECAST,company.id,user.id,dataset.id,30,material_codes=['NOPE'])):
            try: provider(bad); raise AssertionError('expected provider failure')
            except (DatasetInputUnavailableError,CapabilityInputValidationError): pass
        print('FORECAST EXECUTOR PROOF PASS',len(result.result['items']),result.duration_ms,flush=True)
    finally:
        session.rollback(); session.query(Dataset).filter_by(source_type=probe).delete(synchronize_session=False); session.query(CompanyEncryptionKey).filter_by(user_id=user.id).delete(synchronize_session=False); session.query(User).filter_by(email=probe+'@example.invalid').delete(synchronize_session=False); session.query(Company).filter_by(tax_id=probe).delete(synchronize_session=False); session.commit(); session.close()

if __name__=='__main__': asyncio.run(main())
