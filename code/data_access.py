"""Read compact containers without changing any stored scientific numeric values."""
from pathlib import Path
from functools import lru_cache
import json
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
STAGES={'first_stage':'A','jointly_trained':'Direct','pgfs_residual':'FrozenAB','inherited_parameters':'Inheritance'}
@lru_cache(None)
def arrays(relative):
    with np.load(ROOT/relative) as z:return {k:z[k] for k in z.files}
def predictions(model):
    z=arrays('evaluation/predictions.npz');return {q:z[model+'_'+q] for q in ['energy','forces','virial']}
def md_curve(case):return arrays('md/curves.npz')[case if isinstance(case,str) else case['key']]
def training_loss(stage):return arrays('training/losses.npz')[stage]
def training_indices(stage,part):
    m=json.loads((ROOT/'records/original_model_manifest.json').read_text())
    return np.array(m['selected'][STAGES[stage]][part+'_indices'],dtype=int)
def training_predictions(stage,part):
    i=training_indices(stage,part);p=predictions(STAGES[stage]);ref=arrays('data/reference_619.npz')
    return {**{q:p[q][i] for q in p},'source_id':ref['source_id'][i]}
