from data_access import predictions,training_predictions,md_curve,training_loss
"""Optional fresh CPU evaluation of the four archived potentials; requires ASE and calorine."""
from pathlib import Path
import argparse,json
import numpy as np
from nep_branch_tools import predict,check_sum
ROOT=Path(__file__).resolve().parents[1]
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--limit',type=int,default=0,help='0 evaluates all 619 frames');p.add_argument('--output',type=Path,default=ROOT/'reproduced/fresh_predictions');a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
    with np.load(ROOT/'data/reference_619.npz') as r:
        n=len(r['N']) if a.limit==0 else min(a.limit,len(r['N']));fs=[dict(n=int(r['N'][i]),pos=r['positions'][i],cell=r['cell'][i]) for i in range(n)]
    for k in ['A','Direct','FrozenAB','Inheritance']:
        pred=predict(ROOT/f'models/trained/{k}.nep',fs);np.savez_compressed(a.output/f'{k}.npz',**pred);print(k,n,'frames',flush=True)
    err=check_sum(ROOT/'models/trained/A.nep',ROOT/'models/trained/frozen_B_component.nep',ROOT/'models/trained/FrozenAB.nep',fs[:2]);(a.output/'branch_sum_check.json').write_text(json.dumps(err,indent=2)+'\n')
if __name__=='__main__':main()
