#!/bin/bash
set -e

export PYTHONUNBUFFERED=1

# Only run ETL if explicitly requested (set AZURE_STORAGE_SKIP_ETL=0 to force)
if [ "${AZURE_STORAGE_SKIP_ETL:-0}" != "1" ]; then
    echo "Running ETL pipeline..."
    python -u etl/etl_pipeline.py 2>&1 | tee /tmp/etl.log &
    ETL_PID=$!
fi

# Start Streamlit so ACA health probe passes
python -u -m streamlit run app/app.py --server.port 8501 --server.address 0.0.0.0 &
STREAMLIT_PID=$!

echo "Streamlit PID: $STREAMLIT_PID"
if [ -n "${ETL_PID:-}" ]; then
    echo "ETL PID: $ETL_PID"
fi

# Keep container alive with Streamlit process
wait $STREAMLIT_PID
