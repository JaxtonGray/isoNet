# This script will be used to run multiple years at the same time and average the results. This is useful for running the model on a large dataset 
# that spans multiple years, and then averaging the results to get a more accurate representation of the data.

# Import necessary libraries
import os, glob, argparse
import pandas as pd
import geopandas as gpd
import numpy as np

# Import the run_models module from the isonet package
import run_models as rm

# Intialize the argument parser
def get_parser():
    parser = argparse.ArgumentParser(description='Run multiple years of data through the isonet model and average the results.')
    parser.add_argument('path', type=str, help='Path to the directory containing the data files (batched CSV files). Use the run directory not the batch_files directory.')
    parser.add_argument('month_batch', type=str, help='The month to run the model on (e.g. "01" for January, "02" for February, etc.)')
    parser.add_argument('--verbose', action='store_true', help='Print verbose output.')
    return parser

# Grab all values from a specified month across all years and all sites
def grab_month(df, month):
    """
    Grab all values from a specified month across all years and all sites.

    Arguments:
        df (geopandas.GeoDataFrame): The input dataframe containing the data. Date column must be in datetime format.
        month (int): The month to grab (1-12).
    Returns:
        geopandas.GeoDataFrame: A dataframe containing only the values from the specified month.
    """
    return df[df['Date'].dt.month == month]

# Get an average of values across all sites from a dataframe
def average_df(df: gpd.GeoDataFrame, value_col: str | list = ['O18_P', 'H2_P']) -> gpd.GeoDataFrame:
    """
    Get an average of values across all years and sites from a dataframe.

    Arguments:
        df (geopandas.GeoDataFrame): The input dataframe containing the data, with a 'Date' column in datetime format and a 'Lat', 'Lon' column.
        value_col (str | list): The column(s) to average. Default is ['O18_P', 'H2_P'].

    Returns:
        geopandas.GeoDataFrame: A dataframe containing the average values across all years and sites, with a 'Date' column in datetime format and a 'Lat', 'Lon' column.
    """
    # Group by the 'Lat', and 'Lon' columns with the mean of the value columns
    if isinstance(value_col, str):
        # If only one value column is specified, convert it to a list
        value_col = [value_col]

    # Group by the 'Lat', and 'Lon' columns with the mean of the value column(s)
    df_mean = df.groupby(['Lat', 'Lon']).agg({col: 'mean' for col in value_col}).reset_index()

    return df_mean

if __name__ == '__main__':
    # Parse the command line arguments
    parser = get_parser()
    args = parser.parse_args()

    # Import the data from the specified path
    files_path = os.path.join(args.path, 'batch_files')
    df = rm.import_batch_data(files_path)[0]

    # Load the model schemes
    schemes = rm.load_schemes()

    # Load models
    models = rm.load_models()
    print(models)

    # Month to run the model on
    month = int(args.month_batch)

    # Grab all values from the specified month across all years and all sites
    df_month = grab_month(df, month)

    # Run the model on the specified month data
    df_month = rm.run_isonet(models, df_month, schemes, verbose=args.verbose)

    # Average the values across all years and sites
    df_avg = average_df(df_month)

    # Save to output_batch_files directory
    os.makedirs(os.path.join(args.path, 'output_batch_files'), exist_ok=True)
    output_path = os.path.join(args.path, 'output_batch_files')
    df_avg.to_csv(os.path.join(output_path, f'averaged_{month:02d}.csv'), index=False)