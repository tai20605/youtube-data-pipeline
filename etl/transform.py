import os
from etl.utils import get_env_variable, setup_logger, BASE_DIR
from google.cloud import bigquery

SQL_FOLDER_PATH = os.path.join(BASE_DIR, "sql")

logger = setup_logger("transform")


def get_bq_client():
    project_id = get_env_variable("GCP_PROJECT_ID")
    return bigquery.Client(project=project_id)


def run_sql_transform(sql_file_path):
    file_name = os.path.basename(sql_file_path)
    logger.info(f"Starting SQL transform: {file_name}...")

    client = None
    try:
        client = get_bq_client()

        with open(sql_file_path, "r", encoding="utf-8") as f:
            sql_content = f.read()

        formatted_sql = sql_content.format(
            project=client.project,
            raw_dataset=get_env_variable("BQ_RAW_DATASET"),
            processed_dataset=get_env_variable("BQ_PROCESSED_DATASET")
        )

        query_job = client.query(formatted_sql)
        query_job.result()  

        logger.info(f"SQL transform completed: {file_name} (Job ID: {query_job.job_id})")
        return query_job

    except Exception as e:
        logger.error(f"Failed to run SQL transform ({file_name}): {e}")
        raise
    finally:
        if client:
            client.close()


def run_all_transforms():
    sql_files = ["transform_videos.sql", "transform_comments.sql"]
    logger.info(f"Running {len(sql_files)} SQL transform file(s)...")

    for file_name in sql_files:
        file_path = os.path.join(SQL_FOLDER_PATH, file_name)
        if os.path.exists(file_path):
            run_sql_transform(file_path)
        else:
            logger.warning(f"SQL file not found: {file_path}")

    logger.info("All SQL transforms completed successfully.")


if __name__ == "__main__":
    run_all_transforms()
