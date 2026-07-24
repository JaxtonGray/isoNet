#!/bin/bash
#SBATCH --account=def-stadnykt-ab
#SBATCH --job-name=FillData_Batch
#SBATCH --nodes=1
#SBATCH --gres=gpu:2
#SBATCH --partition=gpu-h100
#SBATCH --cpus-per-task=16
#SBATCH --mem=64G
#SBATCH --time=05:00:00
#SBATCH --mail-user=jaxton.gray@ucalgary.ca
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH --array=1-19
#SBATCH --output=slurm_logs/fill_data_%A_%a.out

# !/bin/bash
# This section will grab the years to run
batchInfo=$(sed -n ${SLURM_ARRAY_TASK_ID}p Global_Modelling/batch_index.txt)

# Split the batchInfo into index and year
IFS=' ' read -ra arr <<< "$batchInfo"
index=${arr[0]}
year=${arr[1]}

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
pip install --no-index pandas geopandas numpy scipy rasterio xarray dask netcdf4

# Run the training script
python src/isonet/fill_data.py global_model/grid_points.geojson --batch_global "$index $year"