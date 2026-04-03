import os
import logging
from datetime import datetime

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient
from azure.storage.fileshare import ShareFileClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

COLUMN_NAMES = [
    "Transaction_unique_identifier", "price", "Date_of_Transfer",
    "postcode", "Property_Type", "Old/New", "Duration", "PAON", "SAON",
    "Street", "Locality", "Town/City", "District", "County",
    "PPDCategory_Type", "Record_Status - monthly_file_only",
]

PROPERTY_TYPE_LABELS = {
    "D": "Detached", "T": "Terraced", "S": "Semi-Detached",
    "F": "Flat", "O": "Other",
}

STORAGE_ACCOUNT = os.getenv("AZURE_STORAGE_ACCOUNT_NAME", "projectstorage123")
BLOB_CONTAINER = "rawdata"
BLOB_NAME = "202304.csv"
FILE_SHARE = "processed"
PROCESSED_FILE = "uk_property_processed.parquet"
CHUNKSIZE = 500_000
TMP_CSV = "/tmp/raw_csv_stream.csv"
TMP_PARQUET = f"/tmp/{PROCESSED_FILE}"


def _blob_client():
    cred = DefaultAzureCredential()
    url = f"https://{STORAGE_ACCOUNT}.blob.core.windows.net"
    svc = BlobServiceClient(account_url=url, credential=cred)
    return svc.get_container_client(BLOB_CONTAINER).get_blob_client(BLOB_NAME)


def _file_client():
    cred = DefaultAzureCredential()
    file_url = f"https://{STORAGE_ACCOUNT}.file.core.windows.net"
    return ShareFileClient(
        account_url=file_url,
        share_name=FILE_SHARE,
        file_path=PROCESSED_FILE,
        credential=cred,
        token_intent="backup",
    )


def clean(chunk: pd.DataFrame) -> pd.DataFrame:
    chunk = chunk.drop_duplicates(subset=["Transaction_unique_identifier"], keep="first")
    chunk["Date_of_Transfer"] = pd.to_datetime(chunk["Date_of_Transfer"], errors="coerce")
    chunk = chunk.dropna(subset=["Transaction_unique_identifier", "price", "Date_of_Transfer", "County"])

    str_cols = [
        "postcode", "Property_Type", "Old/New", "Duration", "PAON", "SAON",
        "Street", "Locality", "Town/City", "District", "County",
        "PPDCategory_Type", "Record_Status - monthly_file_only",
    ]
    for col in str_cols:
        if col in chunk.columns:
            chunk[col] = chunk[col].fillna("")

    chunk["price"] = pd.to_numeric(chunk["price"], errors="coerce").fillna(0).astype(int)
    return chunk


def transform(chunk: pd.DataFrame, is_first: bool, q: dict | None = None):
    chunk["year"] = chunk["Date_of_Transfer"].dt.year
    chunk["month"] = chunk["Date_of_Transfer"].dt.month
    chunk["county_upper"] = chunk["County"].str.upper().str.strip()
    chunk["property_type_label"] = chunk["Property_Type"].map(PROPERTY_TYPE_LABELS).fillna("Other")
    chunk["old_new_label"] = chunk["Old/New"].map({"Y": "New Build", "N": "Existing"})
    chunk["duration_label"] = chunk["Duration"].map({"F": "Freehold", "L": "Leasehold"})

    if is_first:
        q = {
            "q1": chunk["price"].quantile(0.25),
            "q2": chunk["price"].quantile(0.50),
            "q3": chunk["price"].quantile(0.75),
        }
        logger.info(f"  Quartiles Q1={q['q1']:,.0f} Q2={q['q2']:,.0f} Q3={q['q3']:,.0f}")

    def bucket(p):
        if p <= q["q1"]:
            return "Low"
        if p <= q["q2"]:
            return "Medium"
        if p <= q["q3"]:
            return "High"
        return "Ultra"

    chunk["price_bucket"] = chunk["price"].apply(bucket)
    return chunk, q


def download_blob_to_tmp():
    logger.info("[STEP 1] Downloading CSV from Blob to /tmp...")
    blob = _blob_client()
    size_gb = blob.get_blob_properties().size / (1024**3)
    logger.info(f"  Blob size: {size_gb:.2f} GB")

    stream = blob.download_blob(max_concurrency=8)
    with open(TMP_CSV, "wb") as f:
        for data in stream.chunks():
            f.write(data)

    logger.info(f"  Saved: {TMP_CSV}")


def process_to_parquet_incremental() -> int:
    logger.info("[STEP 2] Processing CSV chunks -> parquet (incremental)...")
    writer = None
    q = None
    total_rows = 0
    chunk_no = 0

    try:
        for chunk_no, chunk in enumerate(
            pd.read_csv(
                TMP_CSV,
                names=COLUMN_NAMES,
                header=None,
                chunksize=CHUNKSIZE,
                dtype={"price": "float64"},
                on_bad_lines="skip",
            ),
            start=1,
        ):
            chunk = clean(chunk)
            chunk, q = transform(chunk, is_first=(chunk_no == 1), q=q)
            total_rows += len(chunk)

            table = pa.Table.from_pandas(chunk, preserve_index=False)
            if writer is None:
                writer = pq.ParquetWriter(TMP_PARQUET, table.schema, compression="snappy")
            writer.write_table(table)

            logger.info(f"  Chunk {chunk_no}: {len(chunk):,} rows")

    finally:
        if writer is not None:
            writer.close()

    size_mb = os.path.getsize(TMP_PARQUET) / (1024**2)
    logger.info(f"  Parquet written: {TMP_PARQUET} ({size_mb:.1f} MB)")
    return total_rows


def upload_parquet_to_fileshare():
    logger.info("[STEP 3] Uploading parquet to File Share...")
    file_client = _file_client()

    try:
        file_client.delete_file()
    except Exception:
        pass

    with open(TMP_PARQUET, "rb") as f:
        file_client.upload_file(f)

    logger.info("[STEP 3] Upload complete")


def cleanup_tmp_files():
    for p in (TMP_CSV, TMP_PARQUET):
        if os.path.exists(p):
            os.remove(p)


def run():
    start = datetime.now()
    logger.info("=" * 60)
    logger.info("ETL started (Blob -> pandas chunks -> File Share)")
    logger.info("=" * 60)

    try:
        download_blob_to_tmp()
        total_rows = process_to_parquet_incremental()
        upload_parquet_to_fileshare()
    finally:
        cleanup_tmp_files()

    total_s = (datetime.now() - start).total_seconds()
    logger.info("=" * 60)
    logger.info(f"DONE in {total_s:.1f}s ({total_s/60:.1f} min)")
    logger.info(f"Rows: {total_rows:,}")
    logger.info("=" * 60)


if __name__ == "__main__":
    run()
