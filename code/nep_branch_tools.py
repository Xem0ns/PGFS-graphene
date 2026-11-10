"""Independent scalar single-element NEP4 branches; export-only exact sum.

No optimization is performed on the merged model. B training uses residual labels.
Supported deliberately: ordinary single-element NEP4, identical cutoffs/bases/l_max.
"""
from pathlib import Path
import hashlib
import re
import numpy as np

ROOT = Path(__file__).resolve().parents[1]

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()

class Model:
    def __init__(self, path):
        self.path = Path(path)
        lines = self.path.read_text().splitlines()
        self.header = [x.split() for x in lines[:6]]
        h = self.header
        if h[0] != ['nep4', '1', 'C']:
            raise ValueError('Only ordinary single-carbon NEP4 is supported (no ZBL/charge).')
        if [x[0] for x in h[1:]] != ['cutoff', 'n_max', 'basis_size', 'l_max', 'ANN']:
            raise ValueError('Unsupported header.')
        if len(h[1]) != 5 or len(h[5]) != 3 or h[5][2] != '0':
            raise ValueError('Unsupported cutoff/ANN header.')
        self.cutoff = tuple(map(float, h[1][1:3]))
        self.neighbors = tuple(map(int, h[1][3:5]))
        self.nr, self.na = [int(v) + 1 for v in h[2][1:]]
        self.br, self.ba = [int(v) + 1 for v in h[3][1:]]
        self.lmax = tuple(map(int, h[4][1:]))
        if self.lmax != (4, 2, 0):
            raise ValueError('This validated implementation supports l_max 4 2 0 only.')
        self.nl = 5
        self.h = int(h[5][1])
        self.d = self.nr + self.na * self.nl
        self.nann = self.h * (self.d + 2) + 1
        self.nc = self.nr * self.br + self.na * self.ba
        self.values = np.asarray([float(v) for line in lines[6:] for v in line.split()])
        if self.values.size != self.nann + self.nc + self.d or not np.isfinite(self.values).all():
            raise ValueError('Parameter count or finite-value check failed.')
        p = self.values
        k = self.h * self.d
        self.w0 = p[:k].reshape(self.h, self.d)
        self.b0 = p[k:k+self.h]
        self.w1 = p[k+self.h:k+2*self.h]
        self.b1 = p[self.nann-1:self.nann]
        k = self.nann
        self.cr = p[k:k+self.nr*self.br].reshape(self.nr, self.br)
        self.ca = p[k+self.nr*self.br:k+self.nc].reshape(self.na, self.ba)
        self.q = p[-self.d:]
        if np.any(self.q <= 0):
            raise ValueError('Nonpositive descriptor scale.')

def write_model(path, header, values):
    Path(path).write_text('\n'.join(' '.join(map(str, r)) for r in header) + '\n' +
                          '\n'.join(f'{float(v):.17g}' for v in values) + '\n')

def merge(a_path, b_path, out):
    a, b = Model(a_path), Model(b_path)
    if (a.cutoff, a.br, a.ba, a.lmax) != (b.cutoff, b.br, b.ba, b.lmax):
        raise ValueError('Branches require matching cutoffs, basis_size and l_max.')
    nr, na, nh = a.nr+b.nr, a.na+b.na, a.h+b.h
    d = nr + na*a.nl
    if nr-1 > 12 or na-1 > 8 or d > 140:
        raise ValueError('Merged model exceeds supported NEP limits.')
    ia = np.r_[np.arange(a.nr), *(nr+l*na+np.arange(a.na) for l in range(a.nl))]
    ib = np.r_[a.nr+np.arange(b.nr), *(nr+l*na+a.na+np.arange(b.na) for l in range(b.nl))]
    w0 = np.zeros((nh, d)); q = np.zeros(d)
    w0[np.ix_(np.arange(a.h), ia)] = a.w0
    w0[np.ix_(a.h+np.arange(b.h), ib)] = b.w0
    q[ia], q[ib] = a.q, b.q
    h = [r.copy() for r in a.header]
    h[1] = ['cutoff', *a.cutoff, *np.maximum(a.neighbors, b.neighbors)]
    h[2] = ['n_max', nr-1, na-1]; h[5] = ['ANN', nh, 0]
    values = np.r_[w0.ravel(), a.b0, b.b0, a.w1, b.w1, a.b1+b.b1,
                   a.cr.ravel(), b.cr.ravel(), a.ca.ravel(), b.ca.ravel(), q]
    write_model(out, h, values)
    Model(out)
    return {'A_channels': ia.tolist(), 'B_channels': ib.tolist(),
            'neurons': nh, 'descriptor_dimension': d, 'n_max': [nr-1, na-1]}

def configuration(path, *, prediction=False, generations=150000, batch=1000):
    m = Model(path)
    text = (f'type 1 C\nversion 4\ncutoff {m.cutoff[0]} {m.cutoff[1]}\n'
            f'n_max {m.nr-1} {m.na-1}\nbasis_size {m.br-1} {m.ba-1}\n'
            f'l_max {" ".join(map(str,m.lmax))}\nneuron {m.h}\n')
    if prediction:
        return text + 'prediction 1\n'
    reg = np.sqrt(91)/1000  # Preserve old 3-neuron model's automatic penalty weight.
    return text + (f'lambda_e 1\nlambda_f 1\nlambda_v 0\nforce_delta 0\n'
                   f'lambda_1 {reg:.12g}\nlambda_2 {reg:.12g}\n'
                   f'batch {batch}\npopulation 50\ngeneration {generations}\n')

def frames(path):
    with Path(path).open() as f:
        while line := f.readline():
            if not line.strip():
                continue
            n = int(line); header = f.readline()
            kv = dict(re.findall(r'(\w+)=("[^"]*"|\S+)', header))
            props = kv['Properties'].strip('"').split(':'); cols = {}; off = 0
            for j in range(0, len(props), 3):
                cols[props[j]] = (off, off+int(props[j+2])); off += int(props[j+2])
            rows = [f.readline() for _ in range(n)]
            if not all(rows): raise ValueError('Truncated xyz.')
            parts = [r.split() for r in rows]
            if cols.get('species') != (0, 1) or any(r[0] != 'C' for r in parts):
                raise ValueError('Expected carbon only.')
            def col(name):
                start, end = cols[name]
                return np.array([r[start:end] for r in parts], float)
            yield dict(n=n, header=header, body=''.join(rows), kv=kv,
                       cell=np.array(kv['Lattice'].strip('"').split(),float).reshape(3,3),
                       pos=col('pos'), forces=col('forces' if 'forces' in cols else 'force'),
                       energy=float(kv['energy']),
                       virial=np.array(kv['virial'].strip('"').split(),float).reshape(3,3))

def geometry_key(f):
    return hashlib.sha256(str(f['n']).encode()+np.round(f['cell'],6).astype('<f8').tobytes()+
                          np.round(f['pos'],5).astype('<f8').tobytes()).hexdigest()

def write_frames(path, fs, predictions=None):
    with Path(path).open('w') as out:
        for i, f in enumerate(fs):
            if predictions is None:
                out.write(f"{f['n']}\n{f['header']}{f['body']}")
                continue
            e = f['energy']-predictions['energy'][i]
            force = f['forces']-predictions['forces'][i]
            virial = f['virial']-predictions['virial'][i]
            kv = {k:v for k,v in f['kv'].items() if k.lower() not in
                  {'energy','free_energy','virial','stress','properties','residual_of'}}
            kv['energy'] = f'{e:.17g}'
            kv['virial'] = '"'+' '.join(f'{x:.17g}' for x in virial.ravel())+'"'
            kv['Properties'] = 'species:S:1:pos:R:3:forces:R:3'
            kv['residual_of'] = 'A_frozen'
            out.write(str(f['n'])+'\n'+' '.join(f'{k}={v}' for k,v in kv.items())+'\n')
            for pos, frc in zip(f['pos'], force):
                out.write('C '+' '.join(f'{v:.17g}' for v in np.r_[pos,frc])+'\n')

def predict(path, fs):
    from ase import Atoms
    from calorine.calculators import CPUNEP
    calc = CPUNEP(str(Path(path).resolve()))
    e, force, virial = [], [], []
    for f in fs:
        a = Atoms('C'+str(f['n']), positions=f['pos'], cell=f['cell'], pbc=True)
        a.calc = calc
        e.append(a.get_potential_energy()); force.append(a.get_forces())
        virial.append(-a.get_stress(voigt=False)*a.get_volume())
    return dict(energy=np.array(e), forces=np.array(force), virial=np.array(virial))

def check_sum(a, b, total, fs):
    pa, pb, pt = [predict(p, fs) for p in (a,b,total)]
    errors = {k:float(np.max(np.abs(pt[k]-pa[k]-pb[k]))) for k in pt}
    limits = {'energy': 2e-7, 'forces': 2e-8, 'virial': 2e-6}
    if any(not np.isfinite(errors[k]) or errors[k] > limits[k] for k in errors):
        raise AssertionError(f'CPU branch-sum validation failed: {errors}')
    return errors
