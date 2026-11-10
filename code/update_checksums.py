"""Update package checksums after intentional documentation changes; never changes scientific files."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
SKIP={'reproduced','work','.git','.venv','__pycache__','mpl_cache','gpumd_mapping_fix','nep_independent_branches'}
def main():
    hashes={}
    for p in sorted(ROOT.rglob('*')):
        rel=p.relative_to(ROOT)
        if not p.is_file() or any(x in SKIP for x in rel.parts) or str(rel)=='records/SHA256SUMS.json':continue
        h=hashlib.sha256()
        with p.open('rb') as f:
            for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
        hashes[str(rel)]=h.hexdigest()
    (ROOT/'records/SHA256SUMS.json').write_text(json.dumps(hashes,indent=2)+'\n')
    print(f'Wrote {len(hashes)} checksums.')
if __name__=='__main__':main()
