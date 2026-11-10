"""Replay an archived MD protocol in a NEW directory, using shared packed initial states."""
from pathlib import Path
import argparse,json,shutil,subprocess,zipfile
from data_access import ROOT
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--case',required=True,help='Case key or original case path from md/cases.json');p.add_argument('--gpumd',type=Path);p.add_argument('--prepare-only',action='store_true');p.add_argument('--output',required=True,type=Path);a=p.parse_args();cases=json.loads((ROOT/'md/cases.json').read_text());matches=[c for c in cases if a.case in (c['case'],c['key'])]
    if len(matches)!=1:p.error('Use a unique case key or original case path from md/cases.json')
    if not a.prepare_only and a.gpumd is None:p.error('Provide --gpumd, or use --prepare-only.')
    c=matches[0];a.output.mkdir(parents=True,exist_ok=False)
    with zipfile.ZipFile(ROOT/'md/inputs.zip') as z:
        (a.output/'model.xyz').write_bytes(z.read(c['input_member']));(a.output/'run.in').write_bytes(z.read(c['protocol_member']))
    shutil.copy2(ROOT/f'models/md_runtime/{c["model"]}.nep',a.output/'nep.txt')
    if not a.prepare_only:
        print('Saved protocol replay; apply structural-event diagnostics separately. Historical live stop monitor is not implemented.',flush=True)
        with (a.output/'log').open('w') as f:subprocess.run([str(a.gpumd.resolve())],cwd=a.output,stdout=f,stderr=subprocess.STDOUT,check=True)
if __name__=='__main__':main()
