from etl.utils import setup_logger, get_env_variable, load_json, get_channel_id, get_extracted_at, get_ingest_date, request_with_retry

logger = setup_logger("extract_videos")

def get_video_ids_from_playlist(playlist_id):
    api_key = get_env_variable("YOUTUBE_API_KEY")
    url = "https://www.googleapis.com/youtube/v3/playlistItems"
    video_ids = []
    next_page_token = None

    while True:
        params = {
            "part": "contentDetails",
            "playlistId": playlist_id,
            "maxResults": 50,
            "key": api_key
        }
        if next_page_token:
            params["pageToken"] = next_page_token

        response = request_with_retry(url, params)
        if response is None:
            logger.error(f"Giving up on playlist {playlist_id}")
            break
        if response.status_code == 200:
            data = response.json()
            for item in data.get("items", []):
                video_id = item.get("contentDetails", {}).get("videoId")
                if video_id:
                    video_ids.append(video_id)
            next_page_token = data.get("nextPageToken")
            if not next_page_token:
                break
        else:
            logger.error(f"Error {response.status_code} for playlist {playlist_id}: {response.text}")
            break

    return video_ids


def get_video_details(video_ids):
    api_key = get_env_variable("YOUTUBE_API_KEY")
    url = "https://www.googleapis.com/youtube/v3/videos"
    video_details = []

    for i in range(0, len(video_ids), 50):
        batch_ids = video_ids[i:i + 50]
        params = {
            "part": "snippet,statistics,contentDetails",
            "id": ",".join(batch_ids),
            "key": api_key
        }
        response = request_with_retry(url, params)
        if response is None:
            logger.error(f"Giving up on video batch {batch_ids}")
            continue
        if response.status_code == 200:
            data = response.json()
            video_details.extend(data.get("items", []))
        else:
            logger.error(f"Error {response.status_code} for video batch {batch_ids}: {response.text}")

    return video_details


def get_all_infomation(channels_info):
    all_videos = []
    curr_extracted_at = get_extracted_at()
    curr_ingest_date = get_ingest_date()

    for channel in channels_info:
        playlist_id = channel.get("uploads_playlist_id")
        video_ids = get_video_ids_from_playlist(playlist_id)
        video_details = get_video_details(video_ids)

        for video in video_details:
            video["channel_id"] = channel.get("channel_id")
            video["artist_name"] = channel.get("artist_name")
            video["source"] = "youtube_api"
            video["extracted_at"] = curr_extracted_at
            video["ingestion_date"] = curr_ingest_date
            all_videos.append(video)

    return all_videos