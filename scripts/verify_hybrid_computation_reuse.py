"""Numerical-equivalence and micro-benchmark proof for hybrid candidate reuse."""
import sys
from pathlib import Path
from time import perf_counter
import numpy as np
from statistics import median
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.analysis.safety_stock import ComprehensiveSafetyStockOptimizer

DATASETS={"regular":([10,11,12,11,13,12,14,13,12,14,15,14,16,15,14,16],14),"intermittent":([0,0,8,0,0,0,12,0,0,7,0,0,0,15,0,0],21),"volatile":([3,22,1,30,8,24,2,35,5,20,4,32,9,28,6,38],10)}
def old_calculate_all(o,w,l,s=.95):
    classic=o.classic_safety_stock(w,l,s); croston=o.croston_method(w,l,s); syntetos=o.syntetos_boylan_method(w,l,s); bootstrap=o.bootstrapping_method(w,l,s); ml=o.ml_based_safety_stock(w,l,s); hybrid=o.hybrid_safety_stock(w,l,s)
    return {'classic_ss':round(classic,2),'croston_ss':round(croston,2),'syntetos_boylan_ss':round(syntetos,2),'bootstrapping_ss':round(bootstrap,2),'ml_ss':round(ml,2),'hybrid_ss':round(hybrid,2)}
def main():
    o=ComprehensiveSafetyStockOptimizer(); hybrids={}
    for name,(w,l) in DATASETS.items():
        np.random.seed(20260807); old=old_calculate_all(o,w,l); np.random.seed(20260807); new=o.calculate_all_methods(w,l); assert old==new,(name,old,new); hybrids[name]=new['hybrid_ss']
    def measure(fn, runs):
        np.random.seed(20260807); started=perf_counter()
        for _ in range(runs):
            for w,l in DATASETS.values(): fn(o,w,l)
        return perf_counter()-started
    measure(old_calculate_all, 2); measure(lambda o,w,l:o.calculate_all_methods(w,l), 2)
    old_trials=[]; new_trials=[]
    for trial in range(8):
        first,second=(old_calculate_all,lambda o,w,l:o.calculate_all_methods(w,l)) if trial%2==0 else (lambda o,w,l:o.calculate_all_methods(w,l),old_calculate_all)
        first_time=measure(first,12); second_time=measure(second,12)
        if trial%2==0: old_trials.append(first_time); new_trials.append(second_time)
        else: new_trials.append(first_time); old_trials.append(second_time)
    old_seconds=median(old_trials); new_seconds=median(new_trials); improvement=(old_seconds-new_seconds)/old_seconds*100
    print(f'HYBRID REUSE PASS old_seconds={old_seconds:.6f} new_seconds={new_seconds:.6f} improvement_percent={improvement:.2f} old_trials={old_trials} new_trials={new_trials} hybrids={hybrids}',flush=True)
if __name__=='__main__': main()
