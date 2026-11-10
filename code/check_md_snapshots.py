"""Validate the retained representative structures against their complete processed MD curves."""
from pathlib import Path
import json
import numpy as np
from scipy.spatial import cKDTree
from data_access import ROOT,arrays,md_curve
def main():
    z=arrays('md/structural_snapshots.npz');cases=json.loads((ROOT/'md/cases.json').read_text());n=len(z['time_ps'])
    for i in range(n):
        case=cases[int(z['case_index'][i])];row=md_curve(case)[int(z['curve_row'][i])];cell=z['cell'][i];pos=z['positions'][i];L=np.diag(cell);np.testing.assert_allclose(cell,np.diag(L),atol=1e-7)
        wrapped=np.minimum(np.mod(pos,L),np.nextafter(L,0));tree=cKDTree(wrapped,boxsize=L);distance=float(tree.query(wrapped,k=2)[0][:,1].min());fraction=float(np.mean(tree.query_ball_point(wrapped,1.85,return_length=True)-1==3));col=6 if case['experiment']=='fixed_strain_holds' else 5
        np.testing.assert_allclose([distance,fraction],[row[col],row[col+1]],rtol=0,atol=1e-8);np.testing.assert_allclose(z['time_ps'][i],row[0],atol=1e-5,rtol=0)
    print(f'PASS: {n} key structures reproduce their curve pair distances and coordination fractions. Full raw trajectories are outside this compact release.')
if __name__=='__main__':main()
