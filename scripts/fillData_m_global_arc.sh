#!/bin/bash
#SBATCH --job-name=FillData_Batch
#SBATCH --nodes=1
#SBATCH --mem=64G
#SBATCH --time=0-05:00:00
#SBATCH --mail-user=jaxton.gray@ucalgary.ca
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH --array=1-19
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --gres=gpu:2
#SBATCH --partition=gpu-a100
#SBATCH --output=slurm_output/fillData_m_global_%A_%a.out

# !/bin/bash
# This section will grab the years to run
batchInfo=$(sed -n ${SLURM_ARRAY_TASK_ID}p Global_Modelling/batch_index.txt)

# Split the batchInfo into index and year
IFS=' ' read -ra arr <<< "$batchInfo"
index=${arr[0]}
year=${arr[1]}

# Set up the environment
pip install pandas geopandas numpy scipy rasterio xarray dask netcdf4

# Run the training script
python src/isonet/fill_data.py global_model/grid_points.geojson --batch_global "$index $year"