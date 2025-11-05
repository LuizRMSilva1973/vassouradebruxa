PRAGMA enable_profiling = 0;

CREATE TABLE IF NOT EXISTS summary_affinities (
  target TEXT,
  ligand TEXT,
  best_affinity_kcal_per_mol DOUBLE,
  mode INTEGER,
  exhaustiveness INTEGER,
  num_modes INTEGER,
  center_x DOUBLE,
  center_y DOUBLE,
  center_z DOUBLE,
  size_x DOUBLE,
  size_y DOUBLE,
  size_z DOUBLE
);

CREATE TABLE IF NOT EXISTS summary_ddg (
  target TEXT,
  ligand TEXT,
  best_affinity_kcal_per_mol DOUBLE,
  mode INTEGER,
  exhaustiveness INTEGER,
  num_modes INTEGER,
  center_x DOUBLE,
  center_y DOUBLE,
  center_z DOUBLE,
  size_x DOUBLE,
  size_y DOUBLE,
  size_z DOUBLE,
  ref_target TEXT,
  ref_affinity_kcal_per_mol DOUBLE,
  ddg_kcal_per_mol DOUBLE
);

CREATE TABLE IF NOT EXISTS scored (
  target TEXT,
  ligand TEXT,
  best_affinity_kcal_per_mol DOUBLE,
  mode TEXT,
  exhaustiveness INTEGER,
  num_modes INTEGER,
  center_x DOUBLE,
  center_y DOUBLE,
  center_z DOUBLE,
  size_x DOUBLE,
  size_y DOUBLE,
  size_z DOUBLE,
  aff_norm DOUBLE,
  ddg_kcal_per_mol DOUBLE,
  ddg_norm DOUBLE,
  xymove DOUBLE,
  score DOUBLE,
  passes_constraints TEXT
);

CREATE TABLE IF NOT EXISTS ranking_overall (
  ligand TEXT,
  target TEXT,
  best_affinity_kcal_per_mol DOUBLE,
  xymove DOUBLE,
  ddg_kcal_per_mol DOUBLE,
  score DOUBLE,
  passes_constraints TEXT
);

CREATE TABLE IF NOT EXISTS ligand_selectivity_summary (
  ligand TEXT,
  best_target TEXT,
  best_affinity_kcal_per_mol DOUBLE,
  ref_target TEXT,
  ref_affinity_kcal_per_mol DOUBLE,
  ddg_best_kcal_per_mol DOUBLE
);

