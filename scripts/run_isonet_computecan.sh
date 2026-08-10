#!/bin/bash
#SBATCH --account=def-stadnykt-ab
#SBATCH --job-name=Run_IsoNet
#SBATCH --nodes=1
#SBATCH --gpus-per-node=h100:1
#SBATCH --cpus-per-task=16
#SBATCH --mem=64000MB
#SBATCH --time=03:00:00
#SBATCH --mail-user=jaxton.gray@ucalgary.ca
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH --output=slurm_output/run_isonet_%A.out

# !/bin/bash

# Set up the environment
module --force purge
module load StdEnv/2023
module load python/3.12
module load hdf5
module load netcdf
module load proj

pwd

virtualenv --no-download $SLURM_TMPDIR/env
source $SLURM_TMPDIR/env/bin/activate
pip install --no-index --upgrade pip
pip install --no-index pandas geopandas numpy keras tensorflow h5py scikit-learn

# Run the training script
python src/isonet/run_models.py "data/global_model/batch_files" --batch