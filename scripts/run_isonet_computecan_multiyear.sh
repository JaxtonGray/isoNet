#!/bin/bash
#SBATCH --account=def-stadnykt-ab
#SBATCH --job-name=Run_IsoNet
#SBATCH --nodes=1
#SBATCH --gpus-per-node=h100:1
#SBATCH --cpus-per-task=16
#SBATCH --mem=80G
#SBATCH --time=02:00:00
#SBATCH --mail-user=jaxton.gray@ucalgary.ca
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH --array=1-3
#SBATCH --output=slurm_output/run_isonet_%A_%a.out

# !/bin/bash
# This section will grab the month to run
month=$(sed -n ${SLURM_ARRAY_TASK_ID}p runs/global_model/batch_months.txt)

# Set up the environment
module --force purge
module load StdEnv/2023
module load python/3.12
module load hdf5
module load netcdf
module load proj

virtualenv --no-download $SLURM_TMPDIR/env
source $SLURM_TMPDIR/env/bin/activate
pip install --no-index --upgrade pip
pip install --no-index pandas geopandas numpy keras tensorflow h5py scikit-learn tqdm

# Run the training script
python -u src/isonet/multiyear_run_average.py "runs/global_model" "$month"
