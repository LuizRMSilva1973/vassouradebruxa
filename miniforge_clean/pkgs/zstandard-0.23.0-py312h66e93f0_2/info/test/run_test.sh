

set -ex



pip check
LD_PRELOAD=$CONDA_PREFIX/lib/libzstd.so python run_test.py
exit 0
