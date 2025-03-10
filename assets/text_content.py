import os 

# Data Sources
CLEMBENCH_RUNS_REPO = "https://raw.githubusercontent.com/clembench/clembench-runs/main/"
REGISTRY_URL = "https://raw.githubusercontent.com/clp-research/clemcore/refs/heads/refactor_model_registry/backends/model_registry.json"
BENCHMARK_FILE = "benchmark_runs.json"

LATENCY_FOLDER = os.path.join("Addenda", "Latency")
RESULT_FILE = "results.csv"
LATENCY_SUFFIX = "_latency.csv"

# Setup Column Names
# Note - Changing this does not affect the already generated csv `merged_data.csv`
# Run `src/process_data.py` for this

DEFAULT_MODEL_NAME = "Unnamed: 0"
DEFAULT_CLEMSCORE = "-, clemscore"

MODEL_NAME = "Model Name"
CLEMSCORE = "Score (0-100)"
LATENCY = "Latency (s)"
PARAMS = "Parameters (B)"
DUMMY_PARAMS = "Parameters Dummy (B)"
RELEASE_DATE = 'Release Date'
OPEN_WEIGHT = 'Open Weight'
LANGS = "Languages"
CONTEXT = "Context Size (k)"
LICENSE_NAME = "License Name"
LICENSE_URL = "License URL"
SINGLE_IMG = "Single Image"
MULT_IMG = "Multi Image"
TEXT = "Text-Only"
AUDIO = "Audio"
VIDEO = "Video"
INPUT = "Input $/1M tokens"
OUTPUT = "Output $/1M tokens"
LICENSE = "License"
TEMP_DATE = "Temp Date"

# UI - HF Sapce
OPEN = "Open-Weight"
COMM = "Commercial"

TITLE = """<h1 align="center" id="space-title"> LLM Calculator ⚖️⚡ 📏💰</h1> <p align="center">Score, latency metrics are based on <a href="https://clembench.github.io/" target="_blank">clembench</a> .</p>"""

HF_REPO = "colab-potsdam/llm-calculator"
# Date Picker (set as Dropdown until datetime object is fixed)
START_YEAR = "2020"
MONTH_MAP = {
    "January": 1,
    "February": 2,
    "March": 3,
    "April": 4,
    "May": 5,
    "June": 6,
    "July": 7,
    "August": 8,
    "September": 9,
    "October": 10,
    "November": 11,
    "December": 12
}
