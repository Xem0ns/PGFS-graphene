"""Verify compact-package checksums and internal input/source archives."""
from pathlib import Path
import hashlib,json,tarfile,zipfile
ROOT=Path(__file__).resolve().parents[1]
def main():
    manifest=json.loads((ROOT/'records/SHA256SUMS.json').read_text());bad=[]
    for name,digest in manifest.items():
        p=ROOT/name
        if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=digest:bad.append(name)
    for p in [ROOT/'data/DFT_settings.zip',ROOT/'training/inputs.zip',ROOT/'md/inputs.zip']:
        with zipfile.ZipFile(p) as z:
            if z.testzip():bad.append(str(p))
    with tarfile.open(ROOT/'software/GPUMD_sources.tar.gz') as t:
        for member in t:
            if member.isfile():t.extractfile(member).read()
    if bad:raise SystemExit('Verification failed: '+', '.join(bad))
    print(f'PASS: {len(manifest)} hashes and all packed input/source archives.')
if __name__=='__main__':main()
