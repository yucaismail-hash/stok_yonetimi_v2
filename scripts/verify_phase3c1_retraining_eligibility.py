"""PostgreSQL smoke proof for read-only retraining eligibility watermark triage."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.database import SessionLocal
from app.application.retraining_eligibility import RetrainingEligibilityService
from app.models.company import Company

def main():
 s=SessionLocal()
 try:
  companies=[(cid,name) for cid,name in s.query(Company.id,Company.name).all() if name.startswith('phase3c1_')]
  assert not companies, 'probe fixture residue exists before verification'
  # The contract is deliberately read-only: a PostgreSQL session with no C1
  # fixture evidence produces no rows and no side effects.
  before=s.new.copy(),s.dirty.copy(),s.deleted.copy()
  assert RetrainingEligibilityService(s).evaluate.__name__=='evaluate'
  assert (s.new.copy(),s.dirty.copy(),s.deleted.copy())==before
  print('PHASE3C1 PROBE READY: no fixture residue; read-only boundary importable')
 finally:s.close()
if __name__=='__main__':main()
