# Script contains utility functions for the isonet package.

# Import necessary libraries
import os, glob
import pandas as pd

# Combine batches of yearly data into a single dataframe
def combine_yearly_batches(data_dir):
    '''Combine batches of yearly data produced from Fill_Data.py into a single dataframe.
    
    Args:
        data_dir (str): The directory containing the yearly data batches.

    Returns:
        pd.DataFrame: A dataframe containing the combined yearly data.
    '''
    # Get a list of all CSV files in the specified directory
    csv_files = glob.glob(os.path.join(data_dir, '*.csv'))

    return pd.concat((pd.read_csv(f) for f in csv_files), ignore_index=True)