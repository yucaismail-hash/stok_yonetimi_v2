"""Focused PostgreSQL proof for Company Learning incremental refresh/recovery."""
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.application.company_learning_materialization import CompanyLearningMaterializationService
from app.application.company_learning_refresh import CompanyLearningRefreshService
from app.application.learning_evidence import LearningEvidenceService
from app.application.pattern_learning_materialization import PatternLearningMaterializationService
from app.application.champion_registry import ChampionRegistryService
from app.database import SessionLocal
from app.models.actuals import ActualWeeklyObservation
from app.models.champion_registry import ChampionRegistryCurrent, ChampionRegistryEntry, ChampionRegistryTransition
from app.models.company import Company
from app.models.company_learning_memory_v2 import CompanyLearningMemoryV2
from app.models.forecast_evaluation import ForecastEvaluation
from app.models.learning_evidence import LearningEvidence
from app.models.model_artifact import ModelArtifact
from app.models.pattern_learning_memory import PatternLearningMemory
from app.models.retraining_job import RetrainingJob
from app.models.runtime import RuntimeExecution
from scripts.support.pattern_intelligence_fixture import create, cleanup


def clear(root):
    s = SessionLocal()
    try:
        # Company projection is dependent only on the fixture's canonical sources.
        s.query(CompanyLearningMemoryV2).filter_by(company_id=root.company_id).delete(synchronize_session=False)
        s.query(LearningEvidence).filter_by(company_id=root.company_id).delete(synchronize_session=False)
        s.query(ChampionRegistryTransition).filter_by(company_id=root.company_id).delete(synchronize_session=False)
        s.query(ChampionRegistryCurrent).filter_by(company_id=root.company_id).delete(synchronize_session=False)
        s.query(ChampionRegistryEntry).filter_by(company_id=root.company_id).delete(synchronize_session=False)
        s.query(PatternLearningMemory).filter_by(company_id=root.company_id).delete(synchronize_session=False)
        s.commit()
    finally:
        s.close()


def row(cid):
    s = SessionLocal()
    try:
        x = s.query(CompanyLearningMemoryV2).filter_by(company_id=cid).one()
        return (x.id, x.row_version, x.source_summary_fingerprint, x.evidence_maturity_score,
                x.evidence_count, x.pattern_memory_scope_count, dict(x.pattern_distribution), dict(x.champion_summary))
    finally:
        s.close()


def side_counts(cid):
    s = SessionLocal()
    try:
        return (s.query(RuntimeExecution).filter_by(company_id=cid).count(),
                s.query(RetrainingJob).filter_by(company_id=cid).count(),
                s.query(ModelArtifact).filter_by(company_id=cid).count(),
                s.query(ForecastEvaluation).filter_by(company_id=cid).count())
    finally:
        s.close()


def observation_id(root, material):
    s = SessionLocal()
    try:
        return s.query(ActualWeeklyObservation).filter_by(company_id=root.company_id, material_code=material,
            demand_type=root.demand_type, period=root.periods[-1]).one().id
    finally:
        s.close()


def main():
    roots = []
    try:
        # A has three canonical pattern scopes; B and C prove exact dirty scope ownership.
        a = create('stable', 'A', 'sales', 'finished_good'); roots.append(a)
        ctx = {'company_id': a.company_id, 'user_id': a.user_id, 'dataset_id': a.dataset_id}
        trend = create('trend', 'TREND', 'sales', 'semi_finished_good', ctx)
        sparse = create('intermittent', 'SPARSE', 'consumption', 'raw_material', ctx)
        b = create('stable', 'B', 'sales', 'finished_good'); roots.append(b)
        c = create('insufficient', 'C', 'sales', 'finished_good'); roots.append(c)
        pm = PatternLearningMaterializationService()
        for fixture in (a, trend, sparse):
            assert pm.materialize(a.company_id, fixture.material_code, fixture.demand_type, fixture.periods[-1]).status == 'CREATED'
        pm.materialize(b.company_id, b.material_code, b.demand_type, b.periods[-1])
        materializer = CompanyLearningMaterializationService()
        zero = materializer.materialize(c.company_id)
        assert zero.status == 'CREATED' and materializer.get_current(c.company_id).evidence_maturity_score == 0
        service = CompanyLearningRefreshService()
        first = service.refresh(a.company_id, source_change_type='PATTERN_MEMORY')
        b_first = service.refresh(b.company_id, source_change_type='PATTERN_MEMORY')
        b_before = row(b.company_id); c_before = row(c.company_id)
        assert first.status == 'CREATED' and row(a.company_id)[5:7] == (3, {'STABLE': 1, 'STRUCTURAL_CHANGE': 1, 'INTERMITTENT': 1})
        # Canonical LearningEvidence change and duplicate delivery are idempotent.
        write = LearningEvidenceService().record_actual_accepted(a.company_id, observation_id(a, 'A'))
        changed = service.refresh(a.company_id, source_change_type='LEARNING_EVIDENCE')
        duplicate = service.refresh(a.company_id, source_change_type='LEARNING_EVIDENCE')
        assert write.status == 'CREATED' and changed.status == 'UPDATED' and duplicate.status == 'UNCHANGED'
        # A durable Champion transition changes only A's source summary.
        ChampionRegistryService().bootstrap(a.company_id, 'A', 'sales', 'finished_good')
        champion = service.refresh(a.company_id, source_change_type='CHAMPION_TRANSITION')
        assert champion.status == 'UPDATED' and row(a.company_id)[7]['promotion_count'] == 0
        # Accepted source extension updates, delayed old semantic snapshot cannot overwrite it.
        old_session = SessionLocal()
        try:
            old_snapshot = materializer._snapshot(old_session, a.company_id)
        finally:
            old_session.close()
        write2 = LearningEvidenceService().record_actual_accepted(a.company_id, observation_id(trend, 'TREND'))
        newer = service.refresh(a.company_id, source_change_type='LEARNING_EVIDENCE')
        assert write2.status == 'CREATED' and newer.status == 'UPDATED'
        assert materializer.persist_snapshot(old_snapshot).status == 'STALE_RESULT'
        # Controlled pre-write failure leaves durable state unchanged; retry uses PostgreSQL only.
        before_failure = row(a.company_id)
        try:
            CompanyLearningRefreshService(before_materialize=lambda *_: (_ for _ in ()).throw(RuntimeError('INJECTED_PRE_WRITE'))).refresh(a.company_id)
        except RuntimeError:
            pass
        assert row(a.company_id) == before_failure
        assert CompanyLearningRefreshService().refresh(a.company_id).status == 'UNCHANGED'
        # A committed response-loss retry must converge without row-version inflation.
        try:
            CompanyLearningRefreshService(after_materialize=lambda _: (_ for _ in ()).throw(RuntimeError('INJECTED_POST_WRITE'))).refresh(a.company_id)
        except RuntimeError:
            pass
        assert CompanyLearningRefreshService().refresh(a.company_id).status == 'UNCHANGED'
        # Genuine independent-session duplicate refresh callers converge on one projection.
        barrier = threading.Barrier(2)
        def concurrent():
            barrier.wait()
            return CompanyLearningRefreshService().refresh(a.company_id)
        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(pool.map(lambda _: concurrent(), range(2)))
        assert all(x.status == 'UNCHANGED' for x in outcomes)
        # Explicit batch A/B leaves C byte-equivalent; no company discovery is available.
        batch = service.refresh_batch(({'company_id': a.company_id, 'source_change_type': 'EXPLICIT_BATCH'},
                                       {'company_id': b.company_id, 'source_change_type': 'EXPLICIT_BATCH'}))
        assert all(x.status == 'UNCHANGED' for x in batch) and row(b.company_id) == b_before and row(c.company_id) == c_before
        # Fresh session reconstructs the same primitive scalar projection.
        fresh = CompanyLearningMaterializationService().get_current(a.company_id)
        assert (fresh.id, fresh.row_version, fresh.source_summary_fingerprint, fresh.evidence_maturity_score) == row(a.company_id)[:4]
        # No downstream actor is invoked; only deliberately bootstrapped Registry source exists.
        assert side_counts(a.company_id) == (0, 0, 0, 0)
        assert b_first.status == 'CREATED'
        print('PHASE3C5B3B PASS', {'pattern': first.status, 'evidence': changed.status,
              'champion': champion.status, 'duplicate': duplicate.status, 'stale': 'STALE_RESULT',
              'concurrent': [x.status for x in outcomes], 'zero_to_learning': zero.status, 'score': float(row(a.company_id)[3])}, flush=True)
    finally:
        for root in reversed(roots):
            clear(root); cleanup(root)
        s = SessionLocal()
        try:
            assert all(s.query(Company).filter_by(id=root.company_id).count() == 0 for root in roots)
        finally:
            s.close()


if __name__ == '__main__':
    main()
