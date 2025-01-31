"""
Collect data from the multiple sources and create a base datafranme for the LLMCalculator table
Latency - https://github.com/clembench/clembench-runs/tree/main/Addenda/Latency
Pricing - pricing.json
Model info - https://github.com/kushal-10/clembench/blob/feat/registry/backends/model_registry_updated.json
"""

import pandas as pd
import json
import requests
from assets.text_content import CLEMBENCH_RUNS_REPO, REGISTRY_URL, BENCHMARK_FILE, LATENCY_FOLDER, RESULT_FILE, LATENCY_SUFFIX
import os

def validate_request(url: str, response) -> bool:
    """
    Validate if an HTTP request was successful.
    
    Args:
        url (str): The URL that was requested
        response (requests.Response): The response object from the request
        
    Returns:
        bool: True if request was successful (status code 200), False otherwise
    """

    if response.status_code != 200:
        print(f"Failed to read file - {url}. Status Code: {response.status_code}")
        return False
    return True

def fetch_benchmark_data(benchmark: str = "text", version_names: list = []) -> tuple:
    """
    Fetch and parse benchmark results and latency data from CSV files.
    
    Args:
        benchmark (str): Type of benchmark to fetch ('text' or 'multimodal')
        version_names (list): List of version names to search through, sorted by latest first
        
    Returns:
        tuple[pd.DataFrame, pd.DataFrame]: A tuple containing:
            - results_df: DataFrame with benchmark results
            - latency_df: DataFrame with latency measurements
            Returns (None, None) if no matching version is found or requests fail
            
    Raises:
        requests.RequestException: If there's an error fetching the data
        pd.errors.EmptyDataError: If CSV file is empty
        pd.errors.ParserError: If CSV parsing fails
    """
    for v in version_names:
        # Check if version matches benchmark type
        is_multimodal = 'multimodal' in v
        if (benchmark == "multimodal") != is_multimodal:
            continue
            
        # Construct URLs
        results_url = os.path.join(CLEMBENCH_RUNS_REPO, v, RESULT_FILE)
        latency_url = os.path.join(CLEMBENCH_RUNS_REPO, LATENCY_FOLDER, v + LATENCY_SUFFIX)
        
        try:
            results = requests.get(results_url)
            latency = requests.get(latency_url)
            
            if validate_request(results_url, results) and validate_request(latency_url, latency):
                # Convert the CSV content to pandas DataFrames
                results_df = pd.read_csv(pd.io.common.StringIO(results.text))
                latency_df = pd.read_csv(pd.io.common.StringIO(latency.text))
                return results_df, latency_df
                
        except requests.RequestException as e:
            print(f"Error fetching data for version {v}: {e}")
        except pd.errors.EmptyDataError:
            print(f"Error: Empty CSV file found for version {v}")
        except pd.errors.ParserError:
            print(f"Error: Unable to parse CSV data for version {v}")
            
    return None, None

def fetch_version_metadata() -> tuple:
    """
    Fetch and process benchmark metadata from the Clembench GitHub repository.
    
    The data is sourced from: https://github.com/clembench/clembench-runs
    Configure the repository path in src/assets/text_content/CLEMBENCH_RUNS_REPO
    
    Returns:
        tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]: A tuple containing:
            - mm_result: Multimodal benchmark results
            - mm_latency: Multimodal latency data
            - text_result: Text benchmark results
            - text_latency: Text latency data
            Returns (None, None, None, None) if the request fails
    """
    json_url = CLEMBENCH_RUNS_REPO + BENCHMARK_FILE
    response = requests.get(json_url)

    # Check if the JSON file request was successful
    if not validate_request(json_url, response):
        return None, None, None, None

    json_data = response.json()
    versions = json_data['versions']

    # Sort the versions in benchmark by latest first
    version_names = sorted(
        [ver['version'] for ver in versions],
        key=lambda v: list(map(int, v[1:].split('_')[0].split('.'))),  
        reverse=True
    )

    # Latency is in  seconds
    mm_result, mm_latency = fetch_benchmark_data("multimodal", version_names)
    text_result, text_latency = fetch_benchmark_data("text", version_names)

    return mm_latency, mm_result, text_latency, text_result

def fetch_registry_data() -> dict:
    """
    Fetch and parse model registry data from the Clembench registry URL.
    
    The data is sourced from the model registry defined in REGISTRY_URL.
    Contains information about various LLM models including their specifications
    and capabilities.
    
    Returns:
        dict: Dictionary containing model registry data.
        Returns None if the request fails or the JSON is invalid.
        
    Raises:
        requests.RequestException: If there's an error fetching the data
        json.JSONDecodeError: If the response cannot be parsed as JSON
    """
    try:
        response = requests.get(REGISTRY_URL)
        if not validate_request(REGISTRY_URL, response):
            return None
            
        return response.json()
        
    except requests.RequestException as e:
        print(f"Error fetching registry data: {e}")
    except json.JSONDecodeError as e:
        print(f"Error parsing registry JSON: {e}")
    
    return None

if __name__=="__main__":
    fetch_version_metadata()
    registry_data = fetch_registry_data()
    print(registry_data[0])

    