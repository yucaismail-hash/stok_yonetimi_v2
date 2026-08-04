from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import *

router = APIRouter(prefix="/sectors", tags=["sectors"])


@router.get("")
def get_sectors(db: Session = Depends(get_db)):
    """Tüm sektörleri getir"""
    sectors = db.query(Sector).order_by(Sector.name).all()
    return [
        {"id": s.id, "name": s.name, "description": s.description}
        for s in sectors
    ]


@router.post("/init-defaults")
def init_default_sectors(db: Session = Depends(get_db)):
    """Varsayılan sektörleri oluştur"""
    defaults = [
        {"name": "OTOMOTIV", "description": "Otomotiv ve Yedek Parça"},
        {"name": "MOBILYA", "description": "Mobilya ve Aksesuarları"},
        {"name": "BEYAZ_ESYA", "description": "Beyaz Eşya ve Elektrikli Ev Aletleri"},
        {"name": "ENERJI", "description": "Enerji ve Yenilenebilir Enerji"},
        {"name": "TEKSTIL", "description": "Tekstil ve Hazır Giyim"},
        {"name": "GIDA", "description": "Gıda ve İçecek"},
        {"name": "TARIM", "description": "Tarım ve Hayvancılık"},
        {"name": "INSHAAT", "description": "İnşaat ve Müteahhitlik"},
        {"name": "SAVUNMA", "description": "Savunma Sanayi"},
        {"name": "HAVACILIK", "description": "Havacılık ve Uzay"},
        {"name": "KIMYA", "description": "Kimya, Petrol ve Plastik"},
        {"name": "CAM", "description": "Cam ve Seramik"},
        {"name": "CIMENTO", "description": "Çimento ve Yapı Malzemeleri"},
        {"name": "MADENCILIK", "description": "Madencilik"},
        {"name": "METAL", "description": "Demir-Çelik ve Metal"},
        {"name": "MAKINE", "description": "Makine ve Ekipman"},
        {"name": "ELEKTRIK", "description": "Elektrik ve Elektronik"},
        {"name": "BILISIM", "description": "Bilişim, Yazılım ve Teknoloji"},
        {"name": "TELEKOM", "description": "Telekomünikasyon"},
        {"name": "LOJISTIK", "description": "Lojistik ve Taşımacılık"},
        {"name": "TURIZM", "description": "Turizm ve Otelcilik"},
        {"name": "PERAKENDE", "description": "Perakende ve Ticaret"},
        {"name": "FINANS", "description": "Finans ve Bankacılık"},
        {"name": "SIGORTA", "description": "Sigortacılık"},
        {"name": "GAYRIMENKUL", "description": "Gayrimenkul"},
        {"name": "EGITIM", "description": "Eğitim"},
        {"name": "SAGLIK", "description": "Sağlık ve İlaç"},
        {"name": "MEDYA", "description": "Medya ve Yayıncılık"},
        {"name": "REKLAM", "description": "Reklam, Pazarlama ve Danışmanlık"},
        {"name": "ATIK", "description": "Atık Yönetimi ve Geri Dönüşüm"},
        {"name": "ORMAN", "description": "Orman Ürünleri ve Kağıt"},
        {"name": "DIGER", "description": "Diğer Sektörler"}
    ]
    
    count = 0
    for sector in defaults:
        existing = db.query(Sector).filter(Sector.name == sector["name"]).first()
        if not existing:
            new_sector = Sector(**sector)
            db.add(new_sector)
            count += 1
    db.commit()
    return {"msg": f"{count} sektör başarıyla oluşturuldu", "total": len(defaults)}