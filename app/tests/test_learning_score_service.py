# tests/test_learning_score_service.py
# Learning Score Service Testleri

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from app.database import Base
from app.models import User, CompanyLearningMemory, AnalysisResult, AnalysisDataset
from app.services.learning_score_service import LearningScoreService


@pytest.fixture
def db_session():
    """Test veritabanı session'ı"""
    engine = create_engine('sqlite:///:memory:')
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def test_user(db_session):
    """Test kullanıcısı"""
    user = User(
        email="test@example.com",
        hashed_password="hashed",
        full_name="Test User",
        token_balance=100
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def score_service(db_session, test_user):
    """Learning Score Service instance'ı"""
    return LearningScoreService(db_session, test_user.id)


def test_score_analysis_count(score_service, db_session, test_user):
    """Analiz sayısı skoru testi"""
    # 5 analiz oluştur
    for i in range(5):
        result = AnalysisResult(
            user_id=test_user.id,
            result_type='forecast_batch',
            data={},
            status='completed'
        )
        db_session.add(result)
    db_session.commit()
    
    score = score_service._score_analysis_count()
    
    assert score['score'] == 15  # 5 * 3 = 15
    assert score['value'] == 5
    assert score['max'] == 30


def test_score_analysis_count_max(score_service, db_session, test_user):
    """Analiz sayısı maksimum skor testi"""
    # 20 analiz oluştur (max 30)
    for i in range(20):
        result = AnalysisResult(
            user_id=test_user.id,
            result_type='forecast_batch',
            data={},
            status='completed'
        )
        db_session.add(result)
    db_session.commit()
    
    score = score_service._score_analysis_count()
    
    assert score['score'] == 30  # max 30
    assert score['value'] == 20


def test_score_verified_rules(score_service, db_session, test_user):
    """Doğrulanmış kural sayısı skoru testi"""
    # 3 doğrulanmış kural oluştur
    for i in range(3):
        rule = CompanyLearningMemory(
            user_id=test_user.id,
            rule_id=f'rule_{i}',
            rule_name=f'Kural {i}',
            rule_type='seasonal',
            confidence_score=0.8,
            is_verified=True,
            is_active=True,
            first_seen_at=datetime.utcnow(),
            last_seen_at=datetime.utcnow()
        )
        db_session.add(rule)
    db_session.commit()
    
    score = score_service._score_verified_rules()
    
    assert score['score'] == 7.5  # 3 * 2.5 = 7.5
    assert score['value'] == 3
    assert score['max'] == 25


def test_score_data_quality(score_service, db_session, test_user):
    """Veri kalitesi skoru testi"""
    dataset = AnalysisDataset(
        user_id=test_user.id,
        product_count=100,
        period_count=52,
        data_points=5200,
        dataset_data={},
        is_active=True
    )
    db_session.add(dataset)
    db_session.commit()
    
    score = score_service._score_data_quality()
    
    # data_points > 10000 için 10 puan, product_count > 50 için 3 puan, period_count > 26 için 3 puan
    assert score['score'] == 16
    assert score['max'] == 20


def test_calculate_learning_score(score_service, db_session, test_user):
    """Öğrenme skoru hesaplama testi"""
    # Analiz oluştur
    for i in range(5):
        result = AnalysisResult(
            user_id=test_user.id,
            result_type='forecast_batch',
            data={},
            status='completed'
        )
        db_session.add(result)
    
    # Doğrulanmış kural oluştur
    for i in range(3):
        rule = CompanyLearningMemory(
            user_id=test_user.id,
            rule_id=f'rule_{i}',
            rule_name=f'Kural {i}',
            rule_type='seasonal',
            confidence_score=0.8,
            is_verified=True,
            is_active=True,
            first_seen_at=datetime.utcnow(),
            last_seen_at=datetime.utcnow()
        )
        db_session.add(rule)
    
    # Dataset oluştur
    dataset = AnalysisDataset(
        user_id=test_user.id,
        product_count=50,
        period_count=26,
        data_points=1300,
        dataset_data={},
        is_active=True
    )
    db_session.add(dataset)
    db_session.commit()
    
    result = score_service.calculate_learning_score()
    
    assert 'score' in result
    assert 'components' in result
    assert 'level' in result
    assert result['score'] > 0
    assert result['score'] <= 100


def test_get_level(score_service):
    """Seviye belirleme testi"""
    assert score_service._get_level(85) == "Uzman"
    assert score_service._get_level(65) == "İleri"
    assert score_service._get_level(45) == "Orta"
    assert score_service._get_level(25) == "Başlangıç"
    assert score_service._get_level(10) == "Öğreniyor"