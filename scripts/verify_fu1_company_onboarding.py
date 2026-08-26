"""Focused PostgreSQL proof for FU1 canonical Company onboarding."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from pathlib import Path
import sys
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy import func

from app.auth import (
    AuthenticatedUserResponse,
    LoginRequest,
    RegisterRequest,
    create_access_token,
    get_current_company_id,
    get_current_user,
    login,
    register,
)
from app.database import SessionLocal
from app.models import (
    ActualWeeklyObservation,
    Company,
    Dataset,
    DecisionFeedbackEvent,
    DecisionSnapshot,
    ForecastVintage,
    LearningEvidence,
    ModelArtifact,
    RuntimeExecution,
    User,
)


PREFIX = "FU1-ONBOARDING-"


@dataclass(frozen=True)
class DomainCounts:
    actuals: int
    datasets: int
    executions: int
    vintages: int
    learning_evidence: int
    artifacts: int
    decisions: int
    feedback: int


def counts(session) -> DomainCounts:
    return DomainCounts(
        actuals=session.query(func.count(ActualWeeklyObservation.id)).scalar(),
        datasets=session.query(func.count(Dataset.id)).scalar(),
        executions=session.query(func.count(RuntimeExecution.execution_id)).scalar(),
        vintages=session.query(func.count(ForecastVintage.id)).scalar(),
        learning_evidence=session.query(func.count(LearningEvidence.id)).scalar(),
        artifacts=session.query(func.count(ModelArtifact.id)).scalar(),
        decisions=session.query(func.count(DecisionSnapshot.id)).scalar(),
        feedback=session.query(func.count(DecisionFeedbackEvent.id)).scalar(),
    )


def clean() -> None:
    session = SessionLocal()
    try:
        companies = session.query(Company).filter(Company.name.like(f"{PREFIX}%")).all()
        company_ids = [company.id for company in companies]
        if company_ids:
            session.query(User).filter(User.company_id.in_(company_ids)).delete(synchronize_session=False)
            session.query(Company).filter(Company.id.in_(company_ids)).delete(synchronize_session=False)
        session.commit()
    finally:
        session.close()


def register_owner(email: str, company_name: str) -> dict:
    session = SessionLocal()
    try:
        return register(
            RegisterRequest(email=email, password="pilot-password-1", full_name="Pilot Owner", company_name=company_name),
            db=session,
        )
    finally:
        session.close()


def main() -> None:
    clean()
    suffix = uuid4().hex[:12]
    email_a = f"{PREFIX.lower()}a-{suffix}@example.test"
    email_b = f"{PREFIX.lower()}b-{suffix}@example.test"
    company_a_name = f"{PREFIX}A-{suffix}"
    company_b_name = f"{PREFIX}B-{suffix}"
    try:
        baseline_session = SessionLocal()
        baseline = counts(baseline_session)
        baseline_session.close()

        started = time.perf_counter()
        registered_a = register_owner(email_a, company_a_name)
        registration_a_ms = (time.perf_counter() - started) * 1000
        started = time.perf_counter()
        registered_b = register_owner(email_b, company_b_name)
        registration_b_ms = (time.perf_counter() - started) * 1000
        assert registered_a["company_id"] != registered_b["company_id"]
        assert registered_a["role"] == "owner"

        session = SessionLocal()
        try:
            owner_a = session.query(User).filter_by(email=email_a).one()
            owner_b = session.query(User).filter_by(email=email_b).one()
            assert owner_a.company_id == __import__("uuid").UUID(registered_a["company_id"])
            assert owner_b.company_id == __import__("uuid").UUID(registered_b["company_id"])
            assert session.query(Company).filter_by(id=owner_a.company_id).one().name == company_a_name
            assert owner_a.hashed_password != "pilot-password-1"
            assert not hasattr(owner_a, "password")
        finally:
            session.close()

        started = time.perf_counter()
        session = SessionLocal()
        try:
            login_a = login(LoginRequest(email=email_a, password="pilot-password-1"), db=session)
            login_b = login(LoginRequest(email=email_b, password="pilot-password-1"), db=session)
        finally:
            session.close()
        login_ms = (time.perf_counter() - started) * 1000
        assert login_a["company_id"] == registered_a["company_id"]
        assert login_b["company_id"] == registered_b["company_id"]

        started = time.perf_counter()
        fresh = SessionLocal()
        try:
            credentials_a = HTTPAuthorizationCredentials(scheme="Bearer", credentials=login_a["access_token"])
            resolved_a = get_current_user(credentials=credentials_a, db=fresh)
            scope_a = get_current_company_id(resolved_a)
            safe_a = AuthenticatedUserResponse.model_validate(resolved_a).model_dump()
            assert scope_a == owner_a_company_id(registered_a)
            assert "hashed_password" not in safe_a
            assert safe_a["company_id"] == scope_a

            forged = create_access_token({"user_id": str(resolved_a.id), "company_id": registered_b["company_id"]})
            forged_user = get_current_user(
                credentials=HTTPAuthorizationCredentials(scheme="Bearer", credentials=forged), db=fresh
            )
            assert get_current_company_id(forged_user) == scope_a
            assert fresh.query(Company).filter(Company.id == get_current_company_id(forged_user)).one().id == scope_a
        finally:
            fresh.close()
        current_user_ms = (time.perf_counter() - started) * 1000

        duplicate_company_before = company_count()
        try:
            register_owner(email_a, f"{PREFIX}duplicate-{suffix}")
            raise AssertionError("duplicate registration unexpectedly succeeded")
        except HTTPException as exc:
            assert exc.status_code == 400
            assert exc.detail == "Bu e-posta adresi zaten kayıtlı"
        assert company_count() == duplicate_company_before

        # Genuine concurrent duplicate-email collision: exactly one Company/User pair may survive.
        race_email = f"{PREFIX.lower()}race-{suffix}@example.test"
        barrier = threading.Barrier(2)
        outcomes: list[str] = []

        def race(name: str) -> None:
            barrier.wait()
            try:
                register_owner(race_email, f"{PREFIX}race-{name}-{suffix}")
                outcomes.append("CREATED")
            except HTTPException as exc:
                outcomes.append(f"HTTP_{exc.status_code}")

        threads = [threading.Thread(target=race, args=("one",)), threading.Thread(target=race, args=("two",))]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        assert sorted(outcomes) == ["CREATED", "HTTP_400"]
        session = SessionLocal()
        try:
            raced = session.query(User).filter_by(email=race_email).all()
            assert len(raced) == 1
            assert session.query(Company).filter_by(id=raced[0].company_id).count() == 1
        finally:
            session.close()

        final_session = SessionLocal()
        try:
            assert counts(final_session) == baseline
        finally:
            final_session.close()
        print("FU1 PASS")
        print(f"registration_ms: A={registration_a_ms:.1f}, B={registration_b_ms:.1f}")
        print(f"login_ms: {login_ms:.1f}")
        print(f"current_user_company_resolution_ms: {current_user_ms:.1f}")
        print("canonical Company + owner User, duplicate handling, fresh session, tenant authority, and zero domain effects verified")
    finally:
        clean()
        residue_session = SessionLocal()
        try:
            assert residue_session.query(Company).filter(Company.name.like(f"{PREFIX}%")).count() == 0
        finally:
            residue_session.close()


def owner_a_company_id(registered: dict):
    from uuid import UUID

    return UUID(registered["company_id"])


def company_count() -> int:
    session = SessionLocal()
    try:
        return session.query(func.count(Company.id)).scalar()
    finally:
        session.close()


if __name__ == "__main__":
    main()
