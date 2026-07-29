# tests/test_learning_engine.py
# Learning Engine Testleri

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta

from app.database import Base
from app.models import User, CompanyLearningMemory, AnalysisResult
from app.services.learning_engine import LearningEngine


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
def learning_engine(db_session, test_user):
    """Learning Engine instance'ı"""
    return LearningEngine(db_session, test_user.id)


def test_detect_seasonal_patterns(learning_engine):
    """Mevsimsel pattern tespit testi"""
    results = [
        {
            'group': 'Ambalaj',
            'has_seasonality': True,
            'seasonality_strength': 0.8,
            'material_code': 'MAT001'
        },
        {
            'group': 'Ambalaj',
            'has_seasonality': True,
            'seasonality_strength': 0.7,
            'material_code': 'MAT002'
        },
        {
            'group': 'Ambalaj',
            'has_seasonality': True,
            'seasonality_strength': 0.9,
            'material_code': 'MAT003'
        },
        {
            'group': 'Elektronik',
            'has_seasonality': False,
            'seasonality_strength': 0.1,
            'material_code': 'MAT004'
        }
    ]
    
    patterns = learning_engine._detect_seasonal_patterns(results)
    
    # Ambalaj grubu için kural oluşmalı
    assert len(patterns) >= 1
    assert patterns[0]['rule_id'] == 'seasonal_ambalaj'
    assert patterns[0]['rule_type'] == 'seasonal'
    assert patterns[0]['pattern_data']['group'] == 'Ambalaj'
    assert patterns[0]['pattern_data']['material_count'] == 3


def test_detect_intermittent_patterns(learning_engine):
    """Aralıklı talep pattern tespit testi"""
    results = [
        {
            'group': 'Yedek Parça',
            'is_intermittent': True,
            'zero_ratio': 0.5,
            'intermittent_level': 'Yüksek Aralıklı',
            'material_code': 'MAT001'
        },
        {
            'group': 'Yedek Parça',
            'is_intermittent': True,
            'zero_ratio': 0.4,
            'intermittent_level': 'Orta Aralıklı',
            'material_code': 'MAT002'
        },
        {
            'group': 'Tüketim',
            'is_intermittent': False,
            'zero_ratio': 0.1,
            'material_code': 'MAT003'
        }
    ]
    
    patterns = learning_engine._detect_intermittent_patterns(results)
    
    assert len(patterns) >= 1
    assert patterns[0]['rule_id'] == 'intermittent_yedek_parça'
    assert patterns[0]['rule_type'] == 'intermittent'


def test_detect_trend_patterns(learning_engine):
    """Trend pattern tespit testi"""
    results = [
        {
            'group': 'Elektronik',
            'trend_direction': 'Artış',
            'trend_percent': 15,
            'material_code': 'MAT001'
        },
        {
            'group': 'Elektronik',
            'trend_direction': 'Artış',
            'trend_percent': 20,
            'material_code': 'MAT002'
        },
        {
            'group': 'Elektronik',
            'trend_direction': 'Artış',
            'trend_percent': 25,
            'material_code': 'MAT003'
        },
        {
            'group': 'Tekstil',
            'trend_direction': 'Azalış',
            'trend_percent': -10,
            'material_code': 'MAT004'
        }
    ]
    
    patterns = learning_engine._detect_trend_patterns(results)
    
    assert len(patterns) >= 1
    assert patterns[0]['rule_id'] == 'trend_elektronik_artış'
    assert patterns[0]['rule_type'] == 'trend'


def test_create_and_update_rule(learning_engine, db_session):
    """Kural oluşturma ve güncelleme testi"""
    pattern = {
        'rule_id': 'test_rule_001',
        'rule_name': 'Test Kuralı',
        'rule_type': 'seasonal',
        'description': 'Test açıklama',
        'pattern_data': {'group': 'Test', 'count': 5},
        'confidence': 0.7
    }
    
    # Yeni kural oluştur
    new_rule = learning_engine._create_rule(pattern)
    assert new_rule['is_new'] == True
    assert new_rule['rule_id'] == 'test_rule_001'
    
    db_session.commit()
    
    # Kuralı getir
    rule = db_session.query(CompanyLearningMemory).filter(
        CompanyLearningMemory.rule_id == 'test_rule_001'
    ).first()
    assert rule is not None
    assert rule.rule_name == 'Test Kuralı'
    assert rule.confidence_score == 0.7
    
    # Kuralı güncelle
    updated_pattern = {
        'rule_id': 'test_rule_001',
        'rule_name': 'Test Kuralı',
        'rule_type': 'seasonal',
        'description': 'Güncellenmiş açıklama',
        'pattern_data': {'group': 'Test', 'count': 10},
        'confidence': 0.9
    }
    
    existing_rules = learning_engine._get_existing_rules()
    existing = existing_rules.get('test_rule_001')
    
    updated_rule = learning_engine._update_rule(existing, updated_pattern)
    assert updated_rule['is_updated'] == True
    assert updated_rule['confidence'] == 0.9
    
    db_session.commit()
    
    # Güncellemeyi kontrol et
    updated = db_session.query(CompanyLearningMemory).filter(
        CompanyLearningMemory.rule_id == 'test_rule_001'
    ).first()
    assert updated.confidence_score == 0.9
    assert updated.usage_count == 1


def test_get_company_memory(learning_engine, db_session, test_user):
    """Şirket hafızasını getirme testi"""
    # Örnek kurallar oluştur
    rules = [
        CompanyLearningMemory(
            user_id=test_user.id,
            rule_id='test_001',
            rule_name='Kural 1',
            rule_type='seasonal',
            description='Açıklama 1',
            confidence_score=0.8,
            usage_count=5,
            first_seen_at=datetime.utcnow(),
            last_seen_at=datetime.utcnow(),
            is_verified=True
        ),
        CompanyLearningMemory(
            user_id=test_user.id,
            rule_id='test_002',
            rule_name='Kural 2',
            rule_type='intermittent',
            description='Açıklama 2',
            confidence_score=0.6,
            usage_count=3,
            first_seen_at=datetime.utcnow(),
            last_seen_at=datetime.utcnow(),
            is_verified=False
        )
    ]
    
    for rule in rules:
        db_session.add(rule)
    db_session.commit()
    
    # Şirket hafızasını getir
    memory = learning_engine.get_company_memory(limit=10)
    
    assert len(memory) == 2
    assert memory[0]['rule_id'] == 'test_001'
    assert memory[0]['is_verified'] == True
    assert memory[1]['rule_id'] == 'test_002'


def test_get_verified_rules(learning_engine, db_session, test_user):
    """Doğrulanmış kuralları getirme testi"""
    rules = [
        CompanyLearningMemory(
            user_id=test_user.id,
            rule_id='test_001',
            rule_name='Kural 1',
            rule_type='seasonal',
            confidence_score=0.8,
            usage_count=5,
            first_seen_at=datetime.utcnow(),
            last_seen_at=datetime.utcnow(),
            is_verified=True
        ),
        CompanyLearningMemory(
            user_id=test_user.id,
            rule_id='test_002',
            rule_name='Kural 2',
            rule_type='intermittent',
            confidence_score=0.6,
            usage_count=3,
            first_seen_at=datetime.utcnow(),
            last_seen_at=datetime.utcnow(),
            is_verified=False
        )
    ]
    
    for rule in rules:
        db_session.add(rule)
    db_session.commit()
    
    # Doğrulanmış kuralları getir
    verified = learning_engine.get_verified_rules()
    
    assert len(verified) == 1
    assert verified[0]['rule_id'] == 'test_001'
    assert verified[0]['is_verified'] == True