import csv
import boto3
import json
import streamlit as st
import time

# Hardcoded file path to your test CSV
CSV_FILE_PATH = "data/mobile-logs.csv"  # update this if needed

# Initialize the Kinesis client
kinesis_client = boto3.client('kinesis', region_name='eu-west-1')

# Set your Kinesis stream name here
STREAM_NAME = "metric-stream"  # <-- replace with your actual stream name

def send_to_kinesis(data):
    # Use some field as partition key. If none is unique, generate a fallback.
    print(f"Sending data to Kinesis: {data}")
    partition_key = data.get("network") or str(time.time())
    kinesis_client.put_record(
        StreamName=STREAM_NAME,
        Data=json.dumps(data),
        PartitionKey=partition_key
    )

def process_file(file_path, num_records=None):
    with open(file_path, mode='r') as file:
        csv_reader = csv.DictReader(file)
        all_rows = list(csv_reader)

    total_records = len(all_rows) if num_records is None else min(len(all_rows), num_records)

    progress_bar = st.progress(0.0)
    progress_text = st.empty()
    stop_button = st.empty()

    processed_count = 0
    should_stop = False

    for row in all_rows:
        if should_stop or (num_records is not None and processed_count >= num_records):
            break

        if stop_button.button("Stop Processing", key=f"stop_button_{processed_count}"):
            should_stop = True
            break

        send_to_kinesis(row)
        processed_count += 1

        progress = min(processed_count / total_records, 1.0)
        progress_bar.progress(progress)
        progress_text.text(f"Processed {processed_count} of {total_records} records")

        time.sleep(0.01)

def main():
    st.title("Kinesis Test Data Uploader")

    record_option = st.radio(
        "Select number of records to process",
        ["All records", "Specific number"]
    )

    num_records = None
    if record_option == "Specific number":
        num_records = st.number_input(
            "Enter number of records to process",
            min_value=1,
            value=10
        )

    if st.button("Start Processing"):
        st.info(f"Processing {num_records or 'all'} records from {CSV_FILE_PATH} to {STREAM_NAME}")
        process_file(CSV_FILE_PATH, num_records)
        st.success("Processing completed!")

if __name__ == "__main__":
    main()
