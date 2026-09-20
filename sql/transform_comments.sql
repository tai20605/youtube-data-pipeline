-- Incremental transform: raw_dataset.comments -> processed_dataset.comments (upsert by comment_id)
MERGE INTO `{project}.{processed_dataset}.comments` AS target
USING (
    SELECT * EXCEPT(rn) FROM (
        SELECT
            artist_name,
            channel_id,
            video_id,
            id AS comment_id,
            parent_id,
            snippet.topLevelComment.snippet.authorDisplayName AS author_name,
            snippet.topLevelComment.snippet.textDisplay AS comment_text,
            snippet.topLevelComment.snippet.publishedAt AS published_at,
            snippet.topLevelComment.snippet.updatedAt AS updated_at,
            SAFE_CAST(snippet.topLevelComment.snippet.likeCount AS INT64) AS like_count,
            SAFE_CAST(snippet.totalReplyCount AS INT64) AS reply_count,
            extracted_at,
            ingestion_date,
            -- Chỉ giữ lần fetch mới nhất của mỗi comment_id
            ROW_NUMBER() OVER (PARTITION BY id ORDER BY extracted_at DESC) AS rn
        FROM `{project}.{raw_dataset}.comments`
    )
    WHERE rn = 1
) AS src
ON target.comment_id = src.comment_id

WHEN MATCHED THEN
    UPDATE SET
        author_name = src.author_name,
        comment_text = src.comment_text,
        updated_at = src.updated_at,
        like_count = src.like_count,
        reply_count = src.reply_count,
        extracted_at = src.extracted_at,
        ingestion_date = src.ingestion_date

WHEN NOT MATCHED THEN
    INSERT (
        artist_name, channel_id, video_id, comment_id, parent_id,
        author_name, comment_text, published_at, updated_at,
        like_count, reply_count, extracted_at, ingestion_date
    )
    VALUES (
        src.artist_name, src.channel_id, src.video_id, src.comment_id, src.parent_id,
        src.author_name, src.comment_text, src.published_at, src.updated_at,
        src.like_count, src.reply_count, src.extracted_at, src.ingestion_date
    );
