# Utility functions for filtering the dataframe

import pandas as pd
import assets.text_content as tc
import calendar
from typing import Union, List
from datetime import datetime

current_year = str(datetime.now().year)

def filter_cols(df):

    df = df[[
    tc.MODEL_NAME, 
    tc.CLEMSCORE,
    tc.INPUT, 
    tc.OUTPUT,
    tc.LATENCY,
    tc.CONTEXT, 
    tc.PARAMS,
    tc.RELEASE_DATE, 
    tc.LICENSE
    ]]
    
    return df


def convert_date_components_to_timestamp(year: str, month: str) -> int:
    """Convert year and month strings to timestamp."""
    # Create a datetime object for the first day of the month
    date_str = f"{year}-{month:02d}-01"
    return int(pd.to_datetime(date_str).timestamp())

def filter_by_date(df: pd.DataFrame, 
                  start_year, start_month,
                  end_year, end_month,
                  date_column: str = tc.RELEASE_DATE) -> pd.DataFrame:
    """
    Filter DataFrame by date range using separate year and month components.
    """
    # All lists are passed at once, so set default values here instead of passing them in args- Overwritten by empty lists
    if not start_year:
        start_year = tc.START_YEAR
    if not end_year:
        end_year = current_year
    
    if not start_month:
        start_month = "January"
    if not end_month:
        end_month = "December"

    try:
        # Convert string inputs to integers for date creation
        start_timestamp = convert_date_components_to_timestamp(
            int(start_year), 
            int(tc.MONTH_MAP[start_month])
        )
        
        end_timestamp = convert_date_components_to_timestamp(
            int(end_year), 
            int(tc.MONTH_MAP[end_month])
        )
        
        # Convert the DataFrame's date column to timestamps for comparison
        date_timestamps = pd.to_datetime(df[date_column]).apply(lambda x: int(x.timestamp()))
        
        # Filter the DataFrame
        return df[
            (date_timestamps >= start_timestamp) & 
            (date_timestamps <= end_timestamp)
        ]
    except (ValueError, TypeError) as e:
        print(f"Error processing dates: {e}")
        return df  # Return unfiltered DataFrame if there's an error


def filter(df, language_list, parameters, input_price, output_price, multimodal,
           context, open_weight, 
           start_year, start_month, end_year, end_month, 
           license ):

    
    if not df.empty:  # Check if df is non-empty
        df = df[df[tc.LANGS].apply(lambda x: all(lang in x for lang in language_list))]

    if not df.empty:
        df = df[(df[tc.DUMMY_PARAMS] >= parameters[0]) & (df[tc.DUMMY_PARAMS] <= parameters[1])]

    if not df.empty:  # Check if df is non-empty
        df = df[(df[tc.INPUT] >= input_price[0]) & (df[tc.INPUT] <= input_price[1])]
    
    if not df.empty:  # Check if df is non-empty
        df = df[(df[tc.OUTPUT] >= output_price[0]) & (df[tc.OUTPUT] <= output_price[1])]

    if not df.empty:  # Check if df is non-empty
        if tc.TEXT in multimodal:
            df = df[(df[tc.SINGLE_IMG] == False) & (df[tc.MULT_IMG] == False) & (df[tc.AUDIO] == False) & (df[tc.VIDEO] == False) ]
        if tc.SINGLE_IMG in multimodal:
            df = df[df[tc.SINGLE_IMG] == True]
        if tc.MULT_IMG in multimodal:
            df = df[df[tc.MULT_IMG] == True]
        if tc.AUDIO in multimodal:
            df = df[df[tc.AUDIO] == True]
        if tc.VIDEO in multimodal:
            df = df[df[tc.VIDEO] == True]

    if not df.empty:  # Check if df is non-empty
        # Convert 'Context Size (k)' to numeric, coercing errors to NaN
        context_size = pd.to_numeric(df['Context Size (k)'], errors='coerce').fillna(0)
        
        # Apply the filter
        df = df[(context_size >= context[0]) & (context_size <= context[1])]

    if not df.empty:  # Check if df is non-empty
        if tc.OPEN in open_weight and tc.COMM not in open_weight:
            df = df[df[tc.OPEN_WEIGHT] == True]
        elif tc.COMM in open_weight and tc.OPEN not in open_weight:
            df = df[df[tc.OPEN_WEIGHT] == False]
        elif tc.OPEN not in open_weight and tc.COMM not in open_weight:
            # Return empty DataFrame with same columns
            df = pd.DataFrame(columns=df.columns)
        
    if not df.empty:  # Check if df is non-empty
        df = df[df[tc.LICENSE_NAME].apply(lambda x: any(lic in x for lic in license))]

    df = filter_by_date(df, start_year, start_month, end_year, end_month, tc.TEMP_DATE)

    df = filter_cols(df)
    df = df.sort_values(by=tc.CLEMSCORE, ascending=False)

    return df  # Return the filtered dataframe
    

