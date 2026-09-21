from google.api_core.exceptions import NotFound
from google.cloud import bigquery
from etl.utils import get_env_variable, setup_logger, BASE_DIR

logger = setup_logger("load")


def get_bq_client():
    project_id = get_env_variable("GCP_PROJECT_ID")
    return bigquery.Client(project=project_id)


def get_last_published_by_channel(dataset, table_name="videos"):
    client = None
    try:
        client = get_bq_client()
        sql = f"""
            SELECT channel_id, MAX(snippet.publishedAt) AS last_published
            FROM `{client.project}.{dataset}.{table_name}`
            WHERE channel_id IS NOT NULL
            GROUP BY channel_id
        """
        return {row.channel_id: row.last_published for row in client.query(sql).result()}
    except NotFound:
        logger.warning(f"Table {dataset}.{table_name} not found, treating as first run (fetch everything).")
        return {}
    finally:
        if client:
            client.close()


def load_to_bigquery(rows, dataset, table_name, write_disposition="WRITE_APPEND"):
    if not rows:
        logger.warning(f"No data to load into table {dataset}.{table_name}")
        return None

    client = None
    try:
        client = get_bq_client()
        table_ref = f"{client.project}.{dataset}.{table_name}"

        schema_path = BASE_DIR / "schema" / f"{table_name}_schema.json"
        schema = client.schema_from_json(str(schema_path))

        logger.info(f"Loading {len(rows)} rows into table {dataset}.{table_name}")

        job_config = bigquery.LoadJobConfig(
            schema=schema,
            write_disposition=write_disposition,
            source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
            ignore_unknown_values=True
        )

        job = client.load_table_from_json(rows, table_ref, job_config=job_config)
        job.result() 

        logger.info(f"Successfully loaded {len(rows)} rows into table {dataset}.{table_name} (Job ID: {job.job_id})")
        return job

    except Exception as e:
        logger.error(f"Failed to load data into BigQuery ({dataset}.{table_name}): {e}")
        raise
    finally:
        if client:
            client.close()


