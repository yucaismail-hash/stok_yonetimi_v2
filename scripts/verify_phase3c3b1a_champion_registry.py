"""PostgreSQL proof for bootstrap-only durable Champion Registry."""
import concurrent.futures
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import xgboost
from uuid_extensions import uuid7

from app.analysis.forecast import DemandForecaster
from app.application.champion_registry import CLASSICAL_STRATEGY, ChampionRegistryService
from app.database import SessionLocal
from app.engine.adapters.forecast_adapter import forecast_adapter
from app.engine.capability_contracts import CapabilityExecutionRequest
from app.engine.capability_registry import Capability
from app.models.champion_registry import ChampionRegistryCurrent, ChampionRegistryEntry, ChampionRegistryTransition
from app.models.company import Company, User


def main():
    session = SessionLocal(); company_id = user_id = other_company_id = other_user_id = None
    try:
        token = "phase3c3b1a_" + str(uuid7()).replace("-", "")
        company = Company(id=uuid7(), name=token, tax_id=token)
        user = User(id=uuid7(), company_id=company.id, email=token + "@x.invalid", hashed_password="x")
        other = Company(id=uuid7(), name=token + "_other", tax_id=token + "_other")
        other_user = User(id=uuid7(), company_id=other.id, email=token + "_other@x.invalid", hashed_password="x")
        session.add_all((company, user, other, other_user)); session.commit()
        company_id, user_id, other_company_id, other_user_id = company.id, user.id, other.id, other_user.id
        service = ChampionRegistryService()
        first = service.bootstrap(company_id, "SKU", "sales", "finished_good", "G", "C")
        again = service.bootstrap(company_id, "SKU", "sales", "raw_material", "changed", "changed")
        assert first.active_entry_id == again.active_entry_id
        assert session.query(ChampionRegistryEntry).filter_by(company_id=company_id, material_code="SKU", demand_type="sales").count() == 1
        assert session.query(ChampionRegistryTransition).filter_by(company_id=company_id, material_code="SKU", demand_type="sales").count() == 1

        # Independent sessions race without any process-local lock.
        barrier = __import__("threading").Barrier(2)
        def concurrent_bootstrap():
            barrier.wait(); return ChampionRegistryService().bootstrap(company_id, "RACE", "sales", "semi_finished_good").active_entry_id
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            race_ids = list(executor.map(lambda _: concurrent_bootstrap(), range(2)))
        assert race_ids[0] == race_ids[1]
        assert session.query(ChampionRegistryEntry).filter_by(company_id=company_id, material_code="RACE", demand_type="sales").count() == 1
        assert session.query(ChampionRegistryCurrent).filter_by(company_id=company_id, material_code="RACE", demand_type="sales").count() == 1
        assert session.query(ChampionRegistryTransition).filter_by(company_id=company_id, material_code="RACE", demand_type="sales").count() == 1

        semi = service.bootstrap(company_id, "SKU", "consumption", "semi_finished_good")
        raw = service.bootstrap(company_id, "RAW", "consumption", "raw_material")
        other_current = service.bootstrap(other_company_id, "SKU", "sales", "finished_good")
        assert len({first.active_entry_id, semi.active_entry_id, raw.active_entry_id, other_current.active_entry_id}) == 4
        entry = service.get_entry(company_id, first.active_entry_id)
        assert entry.entry_type == "classical_existing" and entry.classical_strategy == CLASSICAL_STRATEGY and entry.product_level == "finished_good"
        assert service.get_entry(other_company_id, first.active_entry_id) is None
        assert service.get_current(other_company_id, "SKU", "sales").active_entry_id == other_current.active_entry_id

        session.expire_all(); entry = session.query(ChampionRegistryEntry).filter_by(id=first.active_entry_id).one()
        transition = session.query(ChampionRegistryTransition).filter_by(destination_entry_id=entry.id).one()
        try:
            entry.classical_strategy = "mutated"; session.flush(); raise AssertionError("entry mutation was allowed")
        except ValueError as exc:
            assert str(exc) == "ChampionRegistryEntry is immutable"; session.rollback()
        transition = session.query(ChampionRegistryTransition).filter_by(id=transition.id).one()
        try:
            transition.reason = "mutated"; session.flush(); raise AssertionError("transition mutation was allowed")
        except ValueError as exc:
            assert str(exc) == "ChampionRegistryTransition is immutable"; session.rollback()

        session.close(); session = SessionLocal()
        fresh = ChampionRegistryService().get_current(company_id, "SKU", "sales")
        assert fresh and fresh.active_entry_id == first.active_entry_id
        assert session.query(ChampionRegistryTransition).filter_by(destination_entry_id=fresh.active_entry_id, transition_type="BOOTSTRAP").count() == 1

        # Forecast remains independent of registry and XGBoost is untouched.
        calls = {"fit": 0, "predict": 0}
        original_fit, original_predict = xgboost.XGBRegressor.fit, xgboost.XGBRegressor.predict
        xgboost.XGBRegressor.fit = lambda *a, **k: (calls.__setitem__("fit", calls["fit"] + 1), original_fit(*a, **k))[1]
        xgboost.XGBRegressor.predict = lambda *a, **k: (calls.__setitem__("predict", calls["predict"] + 1), original_predict(*a, **k))[1]
        try:
            request = CapabilityExecutionRequest(uuid7(), "registry-non-interference", "forecast", Capability.DEMAND_FORECAST, company_id, user_id, uuid7(), 30, params={"horizon": 2})
            result = forecast_adapter(DemandForecaster, {"items": [{"material_code": "SKU", "demand_history": [10, 11, 12, 13, 14, 15, 16, 17]}]}, request)
            assert result["items"][0]["model_used"] in {"holt_winters", "arima", "simple"}
            assert calls == {"fit": 0, "predict": 0}
        finally: xgboost.XGBRegressor.fit, xgboost.XGBRegressor.predict = original_fit, original_predict
        print("PHASE3C3B1A PASS", {"entries": 5, "pointers": 5, "transitions": 5, "concurrent": "one", "xgboost_calls": calls})
    finally:
        if session:
            if company_id:
                for cid in (company_id, other_company_id):
                    pointer_ids = [row[0] for row in session.query(ChampionRegistryCurrent.id).filter_by(company_id=cid)]
                    entry_ids = [row[0] for row in session.query(ChampionRegistryEntry.id).filter_by(company_id=cid)]
                    session.query(ChampionRegistryCurrent).filter(ChampionRegistryCurrent.id.in_(pointer_ids)).delete(synchronize_session=False)
                    session.query(ChampionRegistryTransition).filter_by(company_id=cid).delete(synchronize_session=False)
                    session.query(ChampionRegistryEntry).filter(ChampionRegistryEntry.id.in_(entry_ids)).delete(synchronize_session=False)
                session.query(User).filter(User.id.in_((user_id, other_user_id))).delete(synchronize_session=False)
                session.query(Company).filter(Company.id.in_((company_id, other_company_id))).delete(synchronize_session=False)
                session.commit()
                assert session.query(ChampionRegistryCurrent).filter(ChampionRegistryCurrent.company_id.in_((company_id, other_company_id))).count() == 0
            session.close()


if __name__ == "__main__": main()
