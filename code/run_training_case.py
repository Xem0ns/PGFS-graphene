"""Reconstruct NEP label files from retained DFT arrays and replay an initial optimizer state in a NEW directory."""
from pathlib import Path
import argparse,shutil,subprocess,zipfile
import numpy as np
from data_access import ROOT,arrays,training_indices,predictions,STAGES

def write_labels(output,stage,part):
    r=arrays('data/reference_619.npz');a=predictions('A') if stage=='pgfs_residual' else None
    with Path(output).open('w') as f:
        for i in training_indices(stage,part):
            energy=r['energy'][i]-(a['energy'][i] if a else 0);force=r['forces'][i]-(a['forces'][i] if a else 0);virial=r['virial'][i]-(a['virial'][i] if a else 0);n=int(r['N'][i])
            cell=' '.join(f'{x:.17g}' for x in r['cell'][i].ravel());w=' '.join(f'{x:.17g}' for x in virial.ravel());residual=' residual_of=A_frozen' if a else ''
            f.write(f'{n}\nLattice="{cell}" Properties=species:S:1:pos:R:3:forces:R:3 energy={energy:.17g} virial="{w}" pbc="T T T" source_id={r["source_id"][i]}{residual}\n')
            for pos,frc in zip(r['positions'][i],force):f.write('C '+' '.join(f'{x:.17g}' for x in np.r_[pos,frc])+'\n')

def prepare(stage,output):
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    with zipfile.ZipFile(ROOT/'training/inputs.zip') as z:
        for name,dest in [('nep.in','nep.in'),('initial.nep.restart','nep.restart'),('AB_initial.nep','AB_initial.nep')]:
            member=stage+'/'+name
            if member in z.namelist():(output/dest).write_bytes(z.read(member))
    write_labels(output/'train.xyz',stage,'train');write_labels(output/'test.xyz',stage,'test')

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--case',required=True,choices=list(STAGES));p.add_argument('--nep',type=Path);p.add_argument('--prepare-only',action='store_true');p.add_argument('--output',required=True,type=Path);a=p.parse_args()
    if not a.prepare_only and a.nep is None:p.error('Provide --nep, or use --prepare-only to export inputs without training.')
    prepare(a.case,a.output)
    if not a.prepare_only:
        with (a.output/'training.log').open('w') as f:subprocess.run([str(a.nep.resolve())],cwd=a.output,stdout=f,stderr=subprocess.STDOUT,check=True)
if __name__=='__main__':main()
