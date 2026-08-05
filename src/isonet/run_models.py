# In this script the models will be used and run against the data that has been setup using the fill_data script

# Import necessary libraries
import os, glob, re
import pandas as pd
import geopandas as gpd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import keras

def modelInfo(modelName, modelGuide=os.path.join('models', 'ModelGuide.csv')):
    '''Load information about the current model from the model guide. This includes the scheme and features used in the model.
    
    Args:
        modelName (str): The name of the model to get information for.
        modelGuide (str): The path to the model guide CSV file. Default is 'models/ModelGuide.csv' (based on operating system).
        
    Returns:
        tuple: A tuple containing the model scheme and a list of the features used in the model.'''
    
    # Load in the model guide
    modelGuideDF = pd.read_csv(modelGuide)

    # Extract scheme from model name
    modelScheme = modelName.split("_")[0]

    # Extract features abbreviations from model name
    modelFeatures_Abb = re.findall(r'.', modelName.split("_")[1])

    modelFeatures = []
    for abb in modelFeatures_Abb:
        features = modelGuideDF[modelGuideDF['Abbreviation'] == abb]['Code_Col'].to_string(index=False)
        # Convert string of features to list based on commas
        features = [f.strip() for f in features.split(',')]
        if len(features) > 0:
            modelFeatures += features

    return modelScheme, modelFeatures
    
def importData(filePath):
    '''Import the data from the specified file path and perform necessary transformations.
    Args:
        filePath (str): The path to the CSV file containing the data.
    Returns:
        tuple: A tuple containing the imported data (as a geodataframe) and the list of old column names.'''
    # Read in the correct file
    dataset = pd.read_csv(filePath)
    oldCols = list(dataset.columns)

    # Remove any units (anything in parentheses)
    codeCols = list(map(lambda x: re.sub(r'\(([^()]*)\)', '', x).strip(), oldCols))
    dataset.columns = codeCols

    # Transform Date into Year and JulianDay_Sin
    dataset['Date'] = pd.to_datetime(dataset['Date'], utc=True)
    dataset['Year'] = dataset['Date'].dt.year
    dataset['JulianDay'] = dataset['Date'].dt.dayofyear
    # Sine transformation to account for cyclical nature of Julian Day
    dataset['JulianDay_Sin'] = np.sin(2*np.pi*dataset['JulianDay']/365) 
    
    #Add year and JulianDay_Sin to oldCols 
    oldCols += ['Year', 'JulianDay_Sin']

    dataset = gpd.GeoDataFrame(dataset, geometry=gpd.points_from_xy(dataset['Lon'], dataset['Lat']), crs='EPSG:4326')
    
    return dataset, oldCols

def import_batch_data(dirPath: str) -> gpd.GeoDataFrame:
    '''Import all CSV files in the specified directory and combine them into a single geodataframe.
    Args:
        dirPath (str): The path to the directory containing the CSV files.
    Returns:
        gpd.GeoDataFrame: The combined geodataframe.'''
    # Get all the CSV files in the specified directory
    csvFiles = glob.glob(os.path.join(dirPath, '*.csv'))
    dataset = pd.concat([pd.read_csv(f) for f in csvFiles], ignore_index=True)
    oldCols = list(dataset.columns)
    
    # Remove any units (anything in parentheses)
    codeCols = list(map(lambda x: re.sub(r'\(([^()]*)\)', '', x).strip(), oldCols))
    dataset.columns = codeCols

    # Transform Date into Year and JulianDay_Sin
    dataset['Date'] = pd.to_datetime(dataset['Date'], utc=True)
    dataset['Year'] = dataset['Date'].dt.year
    dataset['JulianDay'] = dataset['Date'].dt.dayofyear
    # Sine transformation to account for cyclical nature of Julian Day
    dataset['JulianDay_Sin'] = np.sin(2*np.pi*dataset['JulianDay']/365) 
    
    #Add year and JulianDay_Sin to oldCols 
    oldCols += ['Year', 'JulianDay_Sin']

    dataset = gpd.GeoDataFrame(dataset, geometry=gpd.points_from_xy(dataset['Lon'], dataset['Lat']), crs='EPSG:4326')
    
    return dataset, oldCols
    

def load_schemes(schemeDir: str = os.path.join('data', 'modelsplit_schemes')) -> dict:
    '''Load the model schemes from the specified scheme file.
    Args:
        schemeDir (str): The directory containing the model scheme files. Default is 'data/modelsplit_schemes' (based on operating system).
    Returns:
        dict: A dictionary containing the model schemes. The keys are the scheme names and the values are the corresponding scheme dataframes.'''

    # Get all the scheme files in the specified directory
    schemeFiles = glob.glob(os.path.join(schemeDir, '*.geojson'))

    # Load each scheme file into a dictionary
    schemes = {}
    for schemeFile in schemeFiles:
        schemeName = os.path.splitext(os.path.basename(schemeFile))[0]
        schemes[schemeName] = gpd.read_file(schemeFile)
    return schemes

def runModel(model: str, inputData: gpd.GeoDataFrame, features: list) -> np.ndarray:
    '''Run the specified model on the provided input data using the given features.
    Args:
        model (str): The path to the model file.
        inputData (gpd.GeoDataFrame): The geodataframe containing the input data to run the model on.
        features (list): A list of features to use for the model.
    Returns:
        numpy.ndarray: The predictions made by the model.'''
    # Extract the features from the input data and scale them
    x = inputData[features].values

    # For some input data and regional schemes, this x may be empty, if so, skip (i.e., return None)
    if x.size == 0:
        return None

    x_scaled = MinMaxScaler().fit_transform(x)

    # Load the model and make predictions

    model = keras.models.load_model(model)
    predictions = model.predict(x_scaled, verbose=0)
    
    return predictions

def run_isonet(models: list, data: gpd.GeoDataFrame, 
               schemes: dict, modelGuide: str = os.path.join('models', 'ModelGuide.csv')):
    '''Run the specified models on the provided data using the given schemes.
    Args:
        models (list): A list of model names to run.
        data (gpd.GeoDataFrame): The geodataframe containing the data to run the models on.
        schemes (dict): A dictionary containing the model schemes.
        modelGuide (str): The path to the model guide CSV file. Default is 'models/ModelGuide.csv' (based on operating system).
    Returns:
        dict: A dictionary containing the results of the model runs. The keys are the model names and the values are the corresponding results.'''

    output = []
    for m in models:
        # Extract model information
        modelType = os.path.dirname(m).split(os.sep)[1]
        modelRun = os.path.dirname(m).split(os.sep)[-1].split("_")[1]
        modelScheme, modelFeatures = modelInfo(modelType, modelGuide=modelGuide)

        # If the model is not a Global scheme, split input data based on geographic scheme
        if modelScheme != 'Global':
            # Get the region from the model name and filter the data based on the region
            modelRegion = os.path.basename(m).split("_")[-2]
            regionGDF = schemes[modelScheme][schemes[modelScheme]['Region'] == modelRegion]
            points_in_region = gpd.clip(data, regionGDF)

            # Run the model on the points in the region and store the predictions
            preds = runModel(m, points_in_region, modelFeatures)
            if preds is not None:
                # Create a new dataframe with the predictions and additional information
                df = points_in_region.copy()
                df[['O18_P', 'H2_P']] = preds
                df['ModelType'] = modelType
                df['ModelRun'] = modelRun
                df['Region'] = modelRegion
                output.append(df)
        else:
            modelRegion = 'Global'
            preds = runModel(m, data, modelFeatures)
            df = data.copy()
            df[['O18_P', 'H2_P']] = preds
            df['ModelType'] = modelType
            df['ModelRun'] = modelRun
            df['Region'] = modelRegion
            output.append(df)

        # Concatenate all the output dataframes into a single dataframe
        output_df = pd.concat(output, ignore_index=True)

    return output_df
            