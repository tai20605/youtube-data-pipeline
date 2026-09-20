-- Incremental transform: raw_dataset.videos -> processed_dataset.videos (upsert by video_id)
MERGE INTO `{project}.{processed_dataset}.videos` AS target
USING (
    SELECT * EXCEPT(rn) FROM (
        SELECT
            artist_name,
            channel_id,
            snippet.channelTitle AS channel_title,
            id AS video_id,
            snippet.title AS video_title,
            snippet.description AS description,
            snippet.publishedAt AS published_at,
            contentDetails.duration AS duration,
            snippet.tags AS tags,
            snippet.categoryId AS category_id,
            SAFE_CAST(statistics.viewCount AS INT64) AS view_count,
            SAFE_CAST(statistics.likeCount AS INT64) AS like_count,
            SAFE_CAST(statistics.commentCount AS INT64) AS comment_count,
            extracted_at,
            source,
            ingestion_date,
            -- Chỉ giữ lần fetch mới nhất của mỗi video_id (raw có thể có nhiều dòng trùng video_id qua các lần chạy)
            ROW_NUMBER() OVER (PARTITION BY id ORDER BY extracted_at DESC) AS rn
        FROM `{project}.{raw_dataset}.videos`
    )
    WHERE rn = 1
) AS src
ON target.video_id = src.video_id

WHEN MATCHED THEN
    UPDATE SET
        channel_title = src.channel_title,
        video_title = src.video_title,
        description = src.description,
        published_at = src.published_at,
        duration = src.duration,
        tags = src.tags,
        category_id = src.category_id,
        view_count = src.view_count,
        like_count = src.like_count,
        comment_count = src.comment_count,
        extracted_at = src.extracted_at,
        source = src.source,
        ingestion_date = src.ingestion_date

WHEN NOT MATCHED THEN
    INSERT (
        artist_name, channel_id, channel_title, video_id, video_title, description,
        published_at, duration, tags, category_id, view_count, like_count, comment_count,
        extracted_at, source, ingestion_date
    )
    VALUES (
        src.artist_name, src.channel_id, src.channel_title, src.video_id, src.video_title, src.description,
        src.published_at, src.duration, src.tags, src.category_id, src.view_count, src.like_count, src.comment_count,
        src.extracted_at, src.source, src.ingestion_date
    );
