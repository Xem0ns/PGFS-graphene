# Data units and containers

`reference_619.npz`: 619 configurations, 160 C atoms per configuration. Energy is total DFT TOTEN/free energy in eV, forces are eV/Å, and virial is the total 3×3 configurational tensor in eV. Positions/cell are Å, N is atom count, area_A2 is the in-plane cross-product area, source_id is the original identifier, and role is the fixed split membership. Engineering strain is (Lx/21.33600913-1)*100 in percent. Two-dimensional tensile stress is -16.021766208*virial/area_A2 in N/m; no effective layer thickness is introduced.

`reference_1171.npz`: cell, positions, forces, energy_free_eV, stress_kbar, and source_id. stress_kbar follows VASP compression-positive stress, not already converted 2D stress. For these orthogonal cells, tensile stress is -stress_kbar*cell_height_A*0.01 in N/m. This collection supports physical characterization and the static reference, not a replacement training split.

`evaluation/predictions.npz`: keys are model_quantity, e.g. A_energy, FrozenAB_forces, Inheritance_virial. All follow the 619-frame reference order. Energy/virial are total configuration values; forces have shape (619,160,3). Absolute labels define energy RMSE. Relative-energy plotting subtracts the respective full curve's first-frame energy per atom only for display.

`training/losses.npz`: a structured array per stage, with named generation/total/L1/L2/energy/force/virial train-validation columns. Energy and virial RMSE are eV/atom; force is eV/Å. Frozen-B native losses refer to residual labels. Complete A+B fitting predictions are reconstructed from saved full-model predictions and exact fitting indices. NEP test.xyz denotes validation, not the extrapolation set.

`md/curves.npz`: keys are mapped by md/cases.json. Continuous tension columns are time_ps, shared_strain_percent, stress_xx_N_m, stress_yy_N_m, T_K, min_pair_A, threefold_fraction, height_RMS_A, Lx_A, Ly_A. Hold columns are time_ps, strain_percent, stress_xx_N_m, stress_yy_N_m, stress_xy_N_m, T_K, min_pair_A, threefold_fraction, height_RMS_A, Lx_A, Ly_A, potential_eV_atom. Complete processed curves are preserved without downsampling or temporal averaging.

`md/structural_snapshots.npz`: positions, cell, time_ps, case_index, curve_row for 37 representative 640-C structures. snapshot_index.json describes their roles. These are not the full raw trajectories. Coordination uses a 1.85 Å cutoff; diagnostics trigger below 99% threefold coordination, below 0.8 Å minimum pair distance, or at nonfinite output.

`md/initial_DFT_comparison.csv`: energy and axial stress errors are signed prediction minus DFT; force error is Cartesian-component RMSE. These labels apply only to the common initial geometries.
