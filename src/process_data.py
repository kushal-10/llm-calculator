import pandas as pd
import json
import os
import pycountry
import re

from src.collect_data import fetch_version_metadata, fetch_registry_data
import assets.text_content as tc

PRICING_PATH = os.path.join('assets', 'pricing.json')

# Convert parameters to float, handling both B and T suffixes
def convert_parameters(param):
    if pd.isna(param) or param == '':
        return None
    param = str(param)
    if 'T' in param:
        return float(param.replace('T', '')) * 1000
    return float(param.replace('B', ''))

# Clean price strings by removing '$' and handling empty strings
def clean_price(price):
    if pd.isna(price) or price == '':
        return None
    return float(price.replace('$', ''))

# Handle language mapping for both string and list inputs
def map_languages(languages):
    if isinstance(languages, float) and pd.isna(languages):
        return None
        
    def get_language_name(lang):
        # Clean and standardize the language code
        lang = str(lang).strip().lower()
        
        # Try to find the language
        try:
            # First try as language code (en, fr, etc.)
            language = pycountry.languages.get(alpha_2=lang)
            if not language:
                # Try as language name (English, French, etc.)
                language = pycountry.languages.get(name=lang.capitalize())
            
            return language.name if language else lang
        except (AttributeError, LookupError):
            return lang
    
    # Handle different input types
    if isinstance(languages, list):
        lang_list = languages
    elif isinstance(languages, str):
        lang_list = [l.strip() for l in languages.split(',')]
    else:
        try:
            lang_list = list(languages)
        except:
            return str(languages)
    
    # Map all languages and join them
    return ', '.join(get_language_name(lang) for lang in lang_list)

# Extract multimodality fields
def get_multimodality_field(model_data, field):
    try:
        return model_data.get('model_config', {}).get('multimodality', {}).get(field, False)
    except:
        return False

def clean_model_name(model_name: str) -> str:
    """Clean model name by removing temperature suffix pattern."""
    # Match pattern like -t0.0--, -t0.7--, -t1.0--, etc.
    pattern = r'-t[0-1]\.[0-9]--'
    return re.split(pattern, model_name)[0]

def merge_data():

    mm_latency_df, mm_result_df, text_latency_df, text_result_df = fetch_version_metadata()

    registry_data = fetch_registry_data()

    with open(PRICING_PATH, 'r') as f:
        pricing_data = json.load(f)

    # Ensure the unnamed column is renamed to 'model'
    mm_result_df.rename(columns={tc.DEFAULT_MODEL_NAME: 'model', tc.DEFAULT_CLEMSCORE: 'clemscore'}, inplace=True)
    text_result_df.rename(columns={tc.DEFAULT_MODEL_NAME: 'model', tc.DEFAULT_CLEMSCORE: 'clemscore'}, inplace=True)
    mm_result_df['model'] = mm_result_df['model'].apply(clean_model_name)
    text_result_df['model'] = text_result_df['model'].apply(clean_model_name)

    # Merge datasets to compute average values
    avg_latency_df = pd.concat([mm_latency_df, text_latency_df], axis=0).groupby('model')['latency'].mean().reset_index()
    avg_clemscore_df = pd.concat([mm_result_df, text_result_df], axis=0).groupby('model')['clemscore'].mean().reset_index()

    # Merge latency, clemscore, registry, and pricing data
    lat_clem_df = pd.merge(avg_latency_df, avg_clemscore_df, on='model', how='outer')

    # Convert registry_data to DataFrame for easier merging
    registry_df = pd.DataFrame(registry_data)
    
    # Extract license info
    registry_df['license_name'] = registry_df['license'].apply(lambda x: x['name'])
    registry_df['license_url'] = registry_df['license'].apply(lambda x: x['url'])

    # Add individual multimodality columns
    registry_df['single_image'] = registry_df.apply(lambda x: get_multimodality_field(x, 'single_image'), axis=1)
    registry_df['multiple_images'] = registry_df.apply(lambda x: get_multimodality_field(x, 'multiple_images'), axis=1)
    registry_df['audio'] = registry_df.apply(lambda x: get_multimodality_field(x, 'audio'), axis=1)
    registry_df['video'] = registry_df.apply(lambda x: get_multimodality_field(x, 'video'), axis=1)

    # Update columns list to include new multimodality fields
    registry_df = registry_df[[
        'model_name', 'parameters', 'release_date', 'open_weight',
        'languages', 'context_size', 'license_name', 'license_url',
        'single_image', 'multiple_images', 'audio', 'video'
    ]]
    
    # Merge with previous data
    merged_df = pd.merge(
        lat_clem_df,
        registry_df,
        left_on='model',
        right_on='model_name',
        how='inner'
    )
    
    # Update column renaming
    merged_df = merged_df.rename(columns={
        'model': tc.MODEL_NAME,
        'latency': tc.LATENCY,
        'clemscore': tc.CLEMSCORE,
        'parameters': tc.PARAMS,
        'release_date': tc.RELEASE_DATE,
        'open_weight': tc.OPEN_WEIGHT,
        'languages': tc.LANGS,
        'context_size': tc.CONTEXT,
        'license_name': tc.LICENSE_NAME,
        'license_url': tc.LICENSE_URL,
        'single_image': tc.SINGLE_IMG,
        'multiple_images': tc.MULT_IMG,
        'audio': tc.AUDIO,
        'video': tc.VIDEO
    })
    
    # Convert pricing_data list to DataFrame
    pricing_df = pd.DataFrame(pricing_data)
    pricing_df['input'] = pricing_df['input'].apply(clean_price)
    pricing_df['output'] = pricing_df['output'].apply(clean_price)
    
    # Merge pricing data with the existing dataframe
    merged_df = pd.merge(
        merged_df,
        pricing_df,
        left_on='Model Name',
        right_on='model_id',
        how='left'
    )
    
    # Drop duplicate model column and rename price columns
    merged_df = merged_df.drop('model_id', axis=1)
    merged_df = merged_df.rename(columns={
        'input': tc.INPUT,
        'output': tc.OUTPUT
    })
    
    # Fill NaN values with 0.0 for pricing columns
    merged_df[tc.INPUT] = merged_df[tc.INPUT].fillna(0.0)
    merged_df[tc.OUTPUT] = merged_df[tc.OUTPUT].fillna(0.0)
    
    # Convert parameters and set to None for commercial models
    merged_df[tc.PARAMS] = merged_df.apply(
        lambda row: None if not row[tc.OPEN_WEIGHT] else convert_parameters(row[tc.PARAMS]), 
        axis=1
    )

    merged_df[tc.LICENSE] = merged_df.apply(
        lambda row: f'[{row[tc.LICENSE_NAME]}]({row[tc.LICENSE_URL]})', axis=1
    )
    merged_df[tc.TEMP_DATE] = merged_df[tc.RELEASE_DATE]

    merged_df[tc.LANGS] = merged_df[tc.LANGS].apply(map_languages)

    # Sort by Clemscore in descending order
    merged_df = merged_df.sort_values(by=tc.CLEMSCORE, ascending=False)
    
    # Drop model_name column
    merged_df.drop(columns=['model_name'], inplace=True)
    
    # Clean up context and convert to integer
    merged_df[tc.CONTEXT] = merged_df[tc.CONTEXT].astype(str).str.replace('k', '', regex=False)
    merged_df[tc.CONTEXT] = pd.to_numeric(merged_df[tc.CONTEXT], errors='coerce').fillna(0).astype(int)

    # Handle commercial model parameters / Set to max of open models
    # Find the maximum value of tc.PARAMS where tc.OPEN_WEIGHT is True
    max_params_value = merged_df.loc[merged_df[tc.OPEN_WEIGHT], tc.PARAMS].max()

    # Create a new dummy PARAM column
    merged_df[tc.DUMMY_PARAMS] = merged_df.apply(
        lambda row: max_params_value if not row[tc.OPEN_WEIGHT] else row[tc.PARAMS],
        axis=1
    )

    return merged_df
