import sqlite3
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = BACKEND_ROOT / "data"
DB_PATH = DATA_DIR / "app.sqlite3"


def init_db(db_path: Path = DB_PATH) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS saved_images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_file_name TEXT NOT NULL,
                stored_file_name TEXT NOT NULL,
                mime_type TEXT NOT NULL,
                format TEXT NOT NULL,
                width INTEGER NOT NULL,
                height INTEGER NOT NULL,
                mode TEXT NOT NULL,
                original_bytes INTEGER NOT NULL,
                saved_bytes INTEGER NOT NULL,
                reduction_rate REAL NOT NULL,
                image_blob BLOB NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


def save_compressed_image(
    *,
    original_file_name: str,
    stored_file_name: str,
    mime_type: str,
    image_format: str,
    width: int,
    height: int,
    mode: str,
    original_bytes: int,
    saved_bytes: int,
    reduction_rate: float,
    image_blob: bytes,
    db_path: Path = DB_PATH,
) -> int:
    init_db(db_path)

    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute(
            """
            INSERT INTO saved_images (
                original_file_name,
                stored_file_name,
                mime_type,
                format,
                width,
                height,
                mode,
                original_bytes,
                saved_bytes,
                reduction_rate,
                image_blob
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                original_file_name,
                stored_file_name,
                mime_type,
                image_format,
                width,
                height,
                mode,
                original_bytes,
                saved_bytes,
                reduction_rate,
                image_blob,
            ),
        )
        return int(cursor.lastrowid)
