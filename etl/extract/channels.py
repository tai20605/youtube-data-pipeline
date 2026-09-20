from etl.utils import setup_logger, get_env_variable, load_json, get_channel_id, request_with_retry

logger = setup_logger("extract_channels")


def get_channel_list(api_key, channel_batch):
    url = "https://www.googleapis.com/youtube/v3/channels"
    params = {
        "part": "contentDetails",
        "id": channel_batch,
        "key": api_key
    }
    response = request_with_retry(url, params)
    if response is None:
        logger.error(f"Giving up on channel batch: {channel_batch}")
        return None
    if response.status_code == 200:
        return response.json()
    else:
        logger.error(f"Error {response.status_code}: {response.text}")
        return None


def get_all_channels_info():
    artists = load_json("config/artists_id.json")
    api_key = get_env_variable("YOUTUBE_API_KEY")

    channel_to_artist = {cid: name for name, cid in artists.items()}
    channel_batches = get_channel_id(artists)
    channels_info = []

    for index, batch in enumerate(channel_batches):
        logger.info(f"Fetching data for batch {index + 1}/{len(channel_batches)}: {batch}")
        data = get_channel_list(api_key, batch)
        if data and "items" in data:
            for item in data["items"]:
                cid = item.get("id")
                uploads_playlist_id = item.get("contentDetails", {}).get("relatedPlaylists", {}).get("uploads")
                artist_name = channel_to_artist.get(cid)

                channels_info.append({
                    "channel_id": cid,
                    "uploads_playlist_id": uploads_playlist_id,
                    "artist_name": artist_name
                })
        else:
            logger.error(f"No data found for batch {index + 1}")

    return channels_info

