# YouTube Data Pipeline

Pipeline thu thập dữ liệu video & comment của top 100 nghệ sĩ US/UK từ YouTube Data API v3, nạp vào BigQuery và xử lý theo mô hình **ELT**.

## Kiến trúc

- **Extract** (`etl/extract/`): gọi YouTube Data API (channels, videos, comments), tự động retry khi gặp lỗi mạng/lỗi 5xx.
- **Load raw** (`etl/load.py`): nạp JSON thô vào `raw_dataset`.
- **Transform** (`etl/transform.py` + `sql/*.sql`): chạy câu lệnh `MERGE` trong BigQuery để upsert từ raw sang `processed_dataset` — video/comment đã tồn tại thì cập nhật (view/like count mới...), chưa có thì thêm mới.
- **Orchestration** (`main.py`): nối toàn bộ 4 bước trên, chạy tuần tự, có log chi tiết.

## Cấu trúc thư mục

```
config/artists_id.json      Danh sách 100 nghệ sĩ + channel_id
etl/extract/                Gọi API: channels.py, videos.py, comments.py
etl/load.py                 Load raw JSON -> BigQuery
etl/transform.py            Chạy SQL transform (raw -> processed) trong BigQuery
etl/utils.py                Helper dùng chung: env, logging, retry
schema/                     Schema BigQuery tường minh cho raw tables
sql/                        Câu lệnh MERGE cho từng bảng processed
main.py                     Entry point, chạy toàn bộ pipeline
```

## Cài đặt

Yêu cầu Python 3.11+.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Tạo file `.env` ở thư mục gốc với các biến:

```
YOUTUBE_API_KEY=...
GCP_PROJECT_ID=...
BQ_RAW_DATASET=...
BQ_PROCESSED_DATASET=...
GOOGLE_APPLICATION_CREDENTIALS=
```

## Chạy pipeline

```bash
python main.py
```

Log ghi vào `logs/pipeline.log`.

## Lên lịch tự động (cron, trên VM)

Trên VM, sau khi đã `git clone` repo và tạo `.venv` ngay trong thư mục repo, cấp quyền chạy cho script:

```bash
chmod +x run_pipeline.sh
```

Thêm vào crontab (`crontab -e`), chạy 07:00 và 23:00 mỗi ngày:

```cron
0 7 * * *  /đường/dẫn/tuyệt/đối/tới/youtube-data-pipeline/run_pipeline.sh
0 23 * * * /đường/dẫn/tuyệt/đối/tới/youtube-data-pipeline/run_pipeline.sh
```
