from etl.utils import setup_logger, get_env_variable, get_extracted_at, get_ingest_date, request_with_retry
logger = setup_logger("extract_comments")

def get_comment_for_video(video_id, max_results=100):
    url = "https://www.googleapis.com/youtube/v3/commentThreads"
    params = {
        "part": "snippet",
        "videoId": video_id,
        "maxResults": min(max_results, 100),
        "textFormat": "plainText",
        "key": get_env_variable("YOUTUBE_API_KEY")
    }
    response = request_with_retry(url, params)
    if response is None:
        logger.error(f"Giving up on comments for video {video_id}")
        return []
    if response.status_code == 200:
        return response.json().get("items", [])
    if response.status_code == 403:
        logger.warning(f"Comments disabled or restricted for video {video_id}.")
        return []
    logger.error(f"Error {response.status_code} fetching comments for video {video_id}: {response.text}")
    return []


def get_all_comments_for_videos(all_videos, top_videos_per_artist=3):
    all_comments = []
    extracted_at = get_extracted_at()
    ingest_date = get_ingest_date()

    # Group videos by artist and select newest videos per artist
    artist_videos_map = {}
    for v in all_videos:
        artist_videos_map.setdefault(v.get("artist_name", "Unknown"), []).append(v)

    selected_videos = []
    for artist, v_list in artist_videos_map.items():
        # Sort by publishedAt descending to get the newest videos
        sorted_by_newest = sorted(v_list, key=lambda v: v.get("snippet", {}).get("publishedAt", ""), reverse=True)
        selected_videos.extend(sorted_by_newest[:top_videos_per_artist])

    logger.info(f"Fetching comments for {len(selected_videos)} newest videos ({top_videos_per_artist} videos/artist)...")

    for idx, video in enumerate(selected_videos, start=1):
        video_id = video.get("id")
        comments = get_comment_for_video(video_id, max_results=100)
        for c in comments:
            c.update({
                "video_id": video_id,
                "channel_id": video.get("channel_id"),
                "artist_name": video.get("artist_name"),
                "parent_id": None,
                "extracted_at": extracted_at,
                "ingestion_date": ingest_date
            })
            all_comments.append(c)

    logger.info(f"Successfully collected {len(all_comments)} comments.")
    return all_comments
