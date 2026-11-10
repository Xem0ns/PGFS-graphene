# PGFS graphene: essential data and code

This compact release supports the strain-trained graphene PGFS study. It retains final potentials, DFT labels and exact splits, predictions, complete processed MD curves, key structures, training inputs, source code, and manuscript figures.

## Contents

| Location | Contents |
|---|---|
| `models/trained/` | First-stage A, jointly trained, PGFS A+B, inherited A+B, and frozen B component |
| `models/md_runtime/` | Same fitted parameters with enlarged neighbor-storage capacity for MD |
| `data/reference_619.npz` | Geometries, energy, forces, virials, identifiers, and roles for the fixed comparison |
| `data/reference_1171.npz` | Full DFT collection for characterization and static stress reference |
| `data/split_manifest.json` | Exact training/validation/holdout/extrapolation membership |
| `evaluation/predictions.npz` | Four models' predictions on all 619 frames, including atomic force components |
| `training/inputs.zip`, `training/losses.npz` | Initial optimizer states, NEP inputs, inherited initial model, and loss histories |
| `md/inputs.zip` | Exact shared initial configurations/velocities and run.in files |
| `md/curves.npz`, `md/cases.json` | Full processed tension curves and 27 holds, with case-to-input mappings |
| `md/structural_snapshots.npz`, `md/snapshot_index.json` | 37 endpoint or pre-event/event structures |
| `software/GPUMD_sources.tar.gz` | Both complete GPUMD/NEP source snapshots, patches, and upstream licenses |
| `figures/manuscript/` | 13 supplied manuscript figure assets |
| `code/`, `records/` | Portable analysis/replay code, model provenance, and checksums |

Historical identifiers: A = First-stage subnetwork; Direct = Jointly trained model; FrozenAB = PGFS model; Inheritance = Inherited-parameter model.

## Reproduce numerical results

Python 3.10 or newer is required. From this directory:

```bash
python -m pip install -r requirements.txt
python code/verify_files.py
python code/reproduce_results.py
python code/reproduce_figures.py
python code/check_md_snapshots.py
```

Outputs go to `reproduced/`. No GPU or new simulations are required. Optional fresh CPU potential evaluation uses ASE/calorine:

```bash
python code/predict_models.py --limit 2
# Omit --limit for all 619 configurations.
```

The fixed extrapolation set contains 330 configurations at strains ≥12%. Energy/force/axial-stress RMSEs are:

| Model | Energy (meV/atom) | Force (eV/Å) | Axial stress (N/m) |
|---|---:|---:|---:|
| First-stage subnetwork | 27.7286 | 0.8277 | 7.1746 |
| Jointly trained model | 41.4499 | 0.4509 | 7.3373 |
| PGFS model | 15.9928 | 0.3238 | 4.1622 |
| Inherited-parameter model | 22.4293 | 0.4674 | 4.4329 |

Model provenance remains in `records/original_model_manifest.json`; this package adds no claim that the evaluation frames were untouched by all historical model choices.

## Compaction scope

Retained numeric values are unchanged. Duplicate XYZ/CSV/NPZ exports are replaced with single lossless containers. The 520 source files are packed, not discarded. Training label files can be reconstructed from DFT arrays and saved A predictions.

Full dump.xyz trajectories, per-frame MD forces/velocities, redundant thermodynamic logs, and historical orchestration scripts are omitted from this compact release. Original experiment directories remain intact locally. Complete processed curves support plotting, curve metrics, and event-time calculations; the 37 saved structures support checking event/endpoint geometry. Independent structural reanalysis of every MD frame requires full raw trajectories outside this release. Do not describe this as a full raw-trajectory archive.

Native NEP test.xyz means in-domain validation, not the extrapolation set. PGFS residual-B labels are DFT minus frozen A; fitting tables use complete A+B predictions against original DFT labels. Original single tensile runs are not replaced with subsequent repeated-run means.

## Replay inputs or calculations

The scripts automatically read the packed inputs. Export to new directories without running a GPU job:

```bash
python code/run_training_case.py --case pgfs_residual --prepare-only --output work/train_inputs
python code/run_md_case.py --case pilot_strain13_seed2026110711_FrozenAB_dt0.125 \
  --prepare-only --output work/hold_inputs
```

Training labels are reconstructed with unchanged numerical content. B replay uses the original frozen A predictions; retraining A requires generating new residual labels. Replay starts from initial optimizer states. Hardware/optimizer variability can change newly fitted weights; use the archived final potentials for reported predictions.

Build the engines only if needed:

```bash
tar -xzf software/GPUMD_sources.tar.gz -C software
make -C software/gpumd_mapping_fix/src -j2 nep gpumd CUDA_ARCH=-arch=sm_120
make -C software/nep_independent_branches/src -j2 nep CUDA_ARCH=-arch=sm_120
```

Set CUDA_ARCH for your GPU. Use mapping-fix NEP for first-stage, joint, and residual-B cases; independent-branch NEP for inheritance. Omit --prepare-only and provide --nep /path/to/nep or --gpumd /path/to/gpumd to launch. MD replay does not implement the historical live structural stop monitor; process completion alone is not a retention result.

## MD and data definitions

Continuous tension: 640 C atoms, target 4.2 K, 0.25 fs timestep, 20 ps equilibration, engineering strain rate 10^8 s^-1, transverse zero pressure, fixed out-of-plane length. Holds: common unmodified DFT geometries replicated to 640 atoms, initial strains 2.0075%, 8.0069%, 13.0064%, 0.125 fs timestep, up to 5 ps, x/z fixed and y at zero pressure, with three paired velocity seeds.

Structural criteria: minimum pair distance <0.8 Å, threefold fraction <99% with a 1.85 Å neighbor cutoff, or nonfinite state. Uniform retrospective checks on saved tension structures do not imply original preregistration for those runs. The criteria are not validated physical fracture criteria. Initial DFT labels do not describe subsequently evolved MD geometries. MD–DFT curve agreement differs from same-geometry prediction accuracy; the combined curve window includes joint post-event output.

Units and array columns are specified in `data/UNITS.md`. GPUMD-derived code retains its GPL license in `software/LICENCE` and the source archive. Original research material licensing and final citation/repository details remain for author completion; see `LICENSE_NOTICE.md`. Read `UPLOAD_GUIDE_zh.md` for Chinese upload instructions.
