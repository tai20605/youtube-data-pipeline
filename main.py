from etl.extract.channels import get_all_channels_info
from etl.extract.videos import get_all_infomation
from etl.extract.comments import get_all_comments_for_videos
from etl.load import load_to_bigquery
from etl.transform import run_all_transforms
from etl.utils import get_env_variable, setup_logger

logger = setup_logger("main")


def main():
    raw_dataset = get_env_variable("BQ_RAW_DATASET")

    logger.info("Step 1/4: Fetching channel info...")
    channels_info = get_all_channels_info()

    logger.info("Step 2/4: Fetching videos...")
    raw_videos = get_all_infomation(channels_info)
    load_to_bigquery(raw_videos, raw_dataset, "videos")

    logger.info("Step 3/4: Fetching comments...")
    raw_comments = get_all_comments_for_videos(raw_videos)
    load_to_bigquery(raw_comments, raw_dataset, "comments")

    logger.info("Step 4/4: Running SQL transform (raw -> processed)...")
    run_all_transforms()

    logger.info("Pipeline finished successfully.")


if __name__ == "__main__":
    main()
