from data_access import predictions,training_predictions,md_curve,training_loss
"""Recompute manuscript metrics from archived reference/prediction arrays (no GPU)."""
from pathlib import Path
import argparse, csv, json
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
NAMES={'A':'First-stage subnetwork','Direct':'Jointly trained model','FrozenAB':'PGFS model','Inheritance':'Inherited-parameter model'}
CONV=16.021766208

def load_npz(path):
    with np.load(path) as d:return {k:d[k] for k in d.files}

def metrics(ref,pred,indices):
    i=np.asarray(indices); n=ref['N'][i]; area=ref['area_A2'][i]
    e=(pred['energy']-ref['energy'][i])/n*1000
    f=pred['forces']-ref['forces'][i]
    s=-(pred['virial'][:,0,0]-ref['virial'][i,0,0])/area*CONV
    return dict(configurations=len(i),energy_RMSE_meV_atom=float(np.sqrt(np.mean(e**2))),force_RMSE_eV_A=float(np.sqrt(np.mean(f**2))),stress_xx_RMSE_N_m=float(np.sqrt(np.mean(s**2))))

def subset(p,i):return {k:p[k][i] for k in ['energy','forces','virial']}

def curve_metrics(ref,curve,left,right):
    x=np.unique(np.r_[left,right,ref[(ref[:,0]>left)&(ref[:,0]<right),0],curve[(curve[:,1]>left)&(curve[:,1]<right),1]])
    rr=np.interp(x,ref[:,0],ref[:,1]);yy=np.interp(x,curve[:,1],curve[:,2]);d=yy-rr;crossing=np.flatnonzero(d[:-1]*d[1:]<0)
    if len(crossing):
        zero=x[crossing]-d[crossing]*(x[crossing+1]-x[crossing])/(d[crossing+1]-d[crossing]);x=np.sort(np.r_[x,zero]);rr=np.interp(x,ref[:,0],ref[:,1]);d=np.interp(x,curve[:,1],curve[:,2])-rr
    numerator=float(np.sum(np.diff(x)*(abs(d[:-1])+abs(d[1:]))/2));denominator=float(np.sum(np.diff(x)*(abs(rr[:-1])+abs(rr[1:]))/2))
    return dict(MAE_N_m=numerator/(right-left),normalized_deviation_percent=100*numerator/denominator)

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,default=ROOT/'reproduced');args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    ref=load_npz(ROOT/'data/reference_619.npz'); assert len(ref['N'])==619
    roles=ref['role']; output={}; rows=[]
    for k,label in NAMES.items():
        p=predictions(k)
        assert p['energy'].shape==(619,) and p['forces'].shape==(619,160,3)
        output[label]={}
        for role in ['low_holdout','extrapolation']:
            i=np.where(roles==role)[0];m=metrics(ref,subset(p,i),i);output[label][role]=m;rows.append(dict(model=label,subset=role,**m))
    # Check against the manuscript's rounded common-configuration values.
    expected={'A':[27.7286,.8277,7.1746],'Direct':[41.4499,.4509,7.3373],'FrozenAB':[15.9928,.3238,4.1622],'Inheritance':[22.4293,.4674,4.4329]}
    for k,v in expected.items():
        m=output[NAMES[k]]['extrapolation'];np.testing.assert_allclose([m['energy_RMSE_meV_atom'],m['force_RMSE_eV_A'],m['stress_xx_RMSE_N_m']],v,rtol=0,atol=1e-4)
    stage_names={'first_stage':'A','jointly_trained':'Direct','pgfs_residual':'FrozenAB','inherited_parameters':'Inheritance'}
    index={str(x):i for i,x in enumerate(ref['source_id'])}
    for stage,k in stage_names.items():
        for part in ['train','test']:
            p=training_predictions(stage,part);i=np.array([index[str(x)] for x in p['source_id']]);m=metrics(ref,p,i)
            # NEP's native test.xyz is the in-domain validation set, not the 330-frame extrapolation set.
            rows.append(dict(model=NAMES[k],subset=f'{stage}_'+('validation' if part=='test' else part),**m))
    fields=list(rows[0]);
    with (args.output/'energy_force_stress_metrics.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
    counts={str(k):int(v) for k,v in zip(*np.unique(roles,return_counts=True))}
    assert counts['extrapolation']==330 and counts['low_holdout']==30
    output['dataset_role_counts']=counts
    p=output['PGFS model']['extrapolation'];j=output['Jointly trained model']['extrapolation']
    output['PGFS_reduction_vs_joint_percent']={k:100*(j[k]-p[k])/j[k] for k in ['energy_RMSE_meV_atom','force_RMSE_eV_A','stress_xx_RMSE_N_m']}
    holds=[]
    for case in json.loads((ROOT/'md/cases.json').read_text()):
        if case['experiment']!='fixed_strain_holds':continue
        curve=md_curve(case);bad=(curve[:,6]<.8)|(curve[:,7]<.99)|~np.isfinite(curve).all(axis=1)
        event=int(np.flatnonzero(bad)[0]) if bad.any() else None
        holds.append(dict(case=case['case'],event_ps=None if event is None else float(curve[event,0]),last_saved_ps=float(curve[-1,0]),completed_5ps=bool(event is None and curve[-1,0]>=5-1e-9)))
    assert len(holds)==27
    output['hold_cases']=holds
    dft=np.loadtxt(ROOT/'data/stress_strain_raw.dat');curves={k:md_curve('tension_'+k) for k in ['Direct','FrozenAB']}
    pgfs=curves['FrozenAB'];first=np.flatnonzero((pgfs[:,5]<.8)|(pgfs[:,6]<.99))[0];end=float(pgfs[first-1,1]);start=float(dft[0,0]);windows=[]
    for name,left,right in [('below_12',start,12.),('extrapolation',12.,end),('combined',start,end)]:
        values={k:curve_metrics(dft,c,left,right) for k,c in curves.items()};reduction=100*(values['Direct']['MAE_N_m']-values['FrozenAB']['MAE_N_m'])/values['Direct']['MAE_N_m'];windows.append(dict(window=name,left_strain_percent=left,right_strain_percent=right,models=values,MAE_reduction_percent=reduction))
    np.testing.assert_allclose([windows[0]['models']['Direct']['MAE_N_m'],windows[0]['models']['FrozenAB']['MAE_N_m'],windows[2]['models']['Direct']['MAE_N_m'],windows[2]['models']['FrozenAB']['MAE_N_m']],[.3411305747345722,.31354748080815215,5.221968500274962,.5192615249466229],rtol=0,atol=1e-8)
    output['continuous_tension_curve_agreement']=windows
    output['continuous_tension_scope']='Independent curves, not same-geometry prediction accuracy; extrapolation and combined windows retain the jointly trained trajectory after its event.'
    (args.output/'summary.json').write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps({'extrapolation_configurations':counts['extrapolation'],'hold_cases':len(holds),'PGFS_reductions_percent':output['PGFS_reduction_vs_joint_percent'],'output':str(args.output)},indent=2))

if __name__=='__main__':main()
