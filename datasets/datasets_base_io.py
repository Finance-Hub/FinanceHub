"""
Base IO code for all FinanceHub test datasets
Author: Gustavo Soares
"""

import os
import pandas as pd

def datasets_path_name() -> str:
    """"
    Returns
    -------
    str : string with datasets path name
    """
    current_directory = os.getcwd()
    return current_directory + r'\data'

def load_data(data_file_name: str) -> pd.DataFrame:
    """
    Loads data from module_path/data/data_file_name.

    Parameters
    ----------
    data_file_name : String. Name of csv file to be loaded from
    module_path/data/data_file_name. For example 'fx_carry.csv'.

    Returns
    -------
    df : Pandas DataFrame typically with dates as index and asset names or symbols as columns
    """

    filename = os.path.join(datasets_path_name(),data_file_name)
    df = pd.read_csv(filename,index_col=0)
    df.index = pd.to_datetime(df.index)
    return df

# FX data loading functions
def load_fx_data(fx_data_feature: str) -> pd.DataFrame:
    """
    Parameters
    ----------
    fx_data_feature : String. Name of fx feature like 'carry' or 'value'

    Returns
    -------
    df : Pandas DataFrame with dates as index and currency symbols as columns
    """
    data_pathname = datasets_path_name()
    fx_data_feature_list = [x.replace('fx_','').replace('.csv','') for x in os.listdir(data_pathname) if x[:3]=='fx_']
    assert(fx_data_feature in fx_data_feature_list),\
                                '%s is not in fx features list: %s' % (fx_data_feature,fx_data_feature_list)
    filename = 'fx_' + fx_data_feature + '.csv'
    df = load_data(filename)
    return df

def load_all_fx_data() -> pd.DataFrame:
    """
    Returns
    -------
    data_dict : A 2 levels multi-index Pandas DataFrames where the index keys are the tuples (date, currency symbols)
                and columns are their features like 'carry' and 'value'
    """
    data_pathname = datasets_path_name()
    fx_files_names = [x for x in os.listdir(data_pathname) if x[:3]=='fx_']
    df_list = [load_data(x) for x in fx_files_names]
    feature_names = [x.replace('fx_','').replace('.csv','') for x in fx_files_names]
    df = pd.concat([df.stack().to_frame(n) for n, df in zip(feature_names,df_list)],
                   join='outer',axis=1,sort=True)
    return df

