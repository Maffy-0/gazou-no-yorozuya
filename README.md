# gazou_no_yorozuya

画像をアップロードし、解像度と品質を選んで圧縮した結果をフロントエンドに表示・ダウンロードするアプリです。

## 構成

- `frontend/`: React + Vite
- `backend/`: FastAPI + Pillow

## 起動方法

### バックエンド

```bash
cd backend
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

確認URL:

```text
http://localhost:8000
```

### フロントエンド

別ターミナルで起動します。

```bash
cd frontend
npm run dev
```

通常は以下で開きます。

```text
http://localhost:5173
```

## 現状の機能

1. フロントエンドで画像ファイルを選択する
2. 解像度プリセットと品質プリセットを選択する
3. `http://localhost:8000/api/compress` に `POST` で送信する
4. バックエンドが画像を圧縮し、画像データと前後情報をJSONで返す
5. 圧縮後の画像、縮小率、変換前後の情報を画面に表示する
6. 圧縮後画像をダウンロードする
7. バックエンド側で `small` / `low` 版をSQLiteに保存する

## API

```text
POST /api/compress
```

フォームデータ:

- `file`: 画像ファイル
- `resolution`: `original` / `medium` / `small`
- `quality`: `high` / `medium` / `low`

レスポンス:

- `application/json`
- 対応形式: JPEG / PNG / WebP
- 出力形式は入力形式を維持

制限:

- アップロード上限: 20MB
- 画像解像度上限: 40MP

## DB保存

`POST /api/compress` の実行時に、保存用として解像度 `small`・品質 `low` の画像を生成し、SQLiteにBLOB保存します。

- DBファイル: `backend/data/app.sqlite3`
- テーブル: `saved_images`
- `backend/data/*.sqlite3` はGit管理対象外

DB確認:

```bash
python backend/scripts/image_db.py list
python backend/scripts/image_db.py schema
```

画像取り出し:

```bash
python backend/scripts/image_db.py export --latest
python backend/scripts/image_db.py export --id 1
python backend/scripts/image_db.py export --all
```

書き出し先は `backend/data/exported/` です。このディレクトリもGit管理対象外です。
