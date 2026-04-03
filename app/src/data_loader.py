"""Data loader for Streamlit dashboard."""

import gc
import os

import pandas as pd
import pyarrow.parquet as pq
import streamlit as st

# Mounted Azure File Share path (ReadOnly)
MOUNT_PATH = "/mnt/processed"
FILE_NAME = "uk_property_processed.parquet"
# Keep memory bounded on 8Gi container
LAST_N_ROW_GROUPS = 2


@st.cache_data(ttl=3600, show_spinner="Loading data...")
def load_data() -> pd.DataFrame:
    """Load last N row groups from parquet (bounded memory)."""
    file_path = os.path.join(MOUNT_PATH, FILE_NAME)
    pf = pq.ParquetFile(file_path)
    num_rgs = pf.metadata.num_row_groups
    start = max(0, num_rgs - LAST_N_ROW_GROUPS)
    row_groups = list(range(start, num_rgs))
    tbl = pf.read_row_groups(row_groups)
    df = tbl.to_pandas()
    del tbl
    gc.collect()
    return df


def get_data() -> pd.DataFrame:
    """Primary data source for app."""
    return load_data()
