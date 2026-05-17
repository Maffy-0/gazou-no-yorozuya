from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = BACKEND_ROOT / "data" / "app.sqlite3"
DEFAULT_EXPORT_DIR = BACKEND_ROOT / "data" / "exported"


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect and export saved images.")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)

    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="List saved image records.")
    list_parser.add_argument("--limit", type=int, default=20)
    list_parser.set_defaults(func=list_images)

    schema_parser = subparsers.add_parser("schema", help="Show saved_images schema.")
    schema_parser.set_defaults(func=show_schema)

    export_parser = subparsers.add_parser("export", help="Export image blobs to files.")
    export_target = export_parser.add_mutually_exclusive_group(required=True)
    export_target.add_argument("--id", type=int, help="Export a record by id.")
    export_target.add_argument("--latest", action="store_true", help="Export latest record.")
    export_target.add_argument("--all", action="store_true", help="Export all records.")
    export_parser.add_argument("--out", type=Path, default=DEFAULT_EXPORT_DIR)
    export_parser.set_defaults(func=export_images)

    args = parser.parse_args()
    args.func(args)


def connect(db_path: Path) -> sqlite3.Connection:
    if not db_path.exists():
        raise SystemExit(f"DB file not found: {db_path}")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def list_images(args: argparse.Namespace) -> None:
    with connect(args.db) as conn:
        rows = conn.execute(
            """
            SELECT
                id,
                original_file_name,
                stored_file_name,
                mime_type,
                width,
                height,
                saved_bytes,
                reduction_rate,
                created_at
            FROM saved_images
            ORDER BY id DESC
            LIMIT ?
            """,
            (args.limit,),
        ).fetchall()

    if not rows:
        print("No saved images.")
        return

    headers = [
        "id",
        "original",
        "stored",
        "mime",
        "size",
        "saved",
        "reduction",
        "created_at",
    ]
    table_rows = [
        [
            str(row["id"]),
            row["original_file_name"],
            row["stored_file_name"],
            row["mime_type"],
            f'{row["width"]}x{row["height"]}',
            format_bytes(row["saved_bytes"]),
            f'{row["reduction_rate"]:.1f}%',
            row["created_at"],
        ]
        for row in rows
    ]

    print_table(headers, table_rows)


def show_schema(args: argparse.Namespace) -> None:
    with connect(args.db) as conn:
        row = conn.execute(
            """
            SELECT sql
            FROM sqlite_master
            WHERE type = 'table'
              AND name = 'saved_images'
            """
        ).fetchone()

    if row is None:
        raise SystemExit("Table not found: saved_images")

    print(row["sql"])


def export_images(args: argparse.Namespace) -> None:
    query = """
        SELECT id, stored_file_name, image_blob
        FROM saved_images
    """
    params: tuple[object, ...] = ()

    if args.id is not None:
        query += " WHERE id = ?"
        params = (args.id,)
    elif args.latest:
        query += " ORDER BY id DESC LIMIT 1"
    else:
        query += " ORDER BY id"

    with connect(args.db) as conn:
        rows = conn.execute(query, params).fetchall()

    if not rows:
        print("No matching images.")
        return

    args.out.mkdir(parents=True, exist_ok=True)

    for row in rows:
        stored_name = Path(row["stored_file_name"]).name
        output_path = args.out / f'{row["id"]}_{stored_name}'
        output_path.write_bytes(row["image_blob"])
        print(output_path)


def print_table(headers: list[str], rows: list[list[str]]) -> None:
    widths = [
        max(len(headers[index]), *(len(row[index]) for row in rows))
        for index in range(len(headers))
    ]

    header_line = "  ".join(
        headers[index].ljust(widths[index]) for index in range(len(headers))
    )
    separator = "  ".join("-" * width for width in widths)

    print(header_line)
    print(separator)
    for row in rows:
        print("  ".join(row[index].ljust(widths[index]) for index in range(len(row))))


def format_bytes(byte_count: int) -> str:
    if byte_count < 1024:
        return f"{byte_count} B"

    megabytes = byte_count / 1024 / 1024
    if megabytes >= 1:
        return f"{megabytes:.2f} MB"

    return f"{byte_count / 1024:.1f} KB"


if __name__ == "__main__":
    main()
