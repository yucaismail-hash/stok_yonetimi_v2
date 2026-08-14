"""Pure non-interference proof: dataset Events remain validation-only, not canonical facts."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.services.dataset.ingestion_policy import validate_events

def main():
 products=[{'Ürün Kodu':'MAT-X','Ürün Grubu':'G1','Ürün Sınıfı':'C1'}]
 valid=[{'Ürün Grubu':'G1','Ürün Sınıfı':'C1','Event Tipi':'campaign','Yıl':2026,'Başlangıç Hafta':10,'Bitiş Hafta':11}]
 invalid=[{**valid[0],'Event Tipi':'weather'}]
 assert validate_events(valid,products)=={'valid':True,'errors':[],'availability':'available'}
 assert validate_events(invalid,products)['valid'] is False
 print('PHASE 3C7B1 DATASET EVENTS BOUNDARY PASS',flush=True)
if __name__=='__main__':main()
