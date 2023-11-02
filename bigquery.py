#bigquery.py
#bigquery.py
from google.cloud import bigquery

def insert_into_bigquery(project_id, dataset_id, table_id, data):
    client = bigquery.Client(project=project_id)
    dataset_ref = client.dataset(dataset_id)
    table_ref = dataset_ref.table(table_id)

    errors = client.insert_rows(table_ref, data)
    if errors:
        raise Exception(f"Error inserting data into BigQuery: {errors}")
