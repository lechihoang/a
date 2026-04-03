"""
Download UK Property Price dataset from Kaggle using curl.
Usage: python etl/download_data.py
"""

import os
import zipfile
import subprocess

KAGGLE_USERNAME = os.getenv("KAGGLE_USERNAME")
KAGGLE_KEY = os.getenv("KAGGLE_KEY")
DATASET = "willianoliveiragibin/uk-property-price-data-1995-2023-04"
ZIP_PATH = "data/uk-property-price.zip"
EXTRACT_DIR = "data/"

def download():
    if not KAGGLE_USERNAME or not KAGGLE_KEY:
        print("ERROR: Set KAGGLE_USERNAME and KAGGLE_KEY in .env")
        print("Get from: https://www.kaggle.com/settings/api")
        return

    url = f"https://www.kaggle.com/api/v1/datasets/download/{DATASET}"

    print("Downloading dataset from Kaggle...")
    result = subprocess.run(
        ["curl", "-L", "-o", ZIP_PATH, "-u", f"{KAGGLE_USERNAME}:{KAGGLE_KEY}", url],
        capture_output=True, text=True
    )

    if result.returncode != 0:
        print("Download failed:", result.stderr)
        return

    print("Extracting...")
    with zipfile.ZipFile(ZIP_PATH, "r") as z:
        z.extractall(EXTRACT_DIR)
        print("Extracted:", z.namelist())

    os.remove(ZIP_PATH)
    print("Done!")

if __name__ == "__main__":
    download()
