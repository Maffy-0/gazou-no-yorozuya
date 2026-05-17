# gazou_no_yorozuya

画像をアップロードし、バックエンドでJPEG圧縮した結果をフロントエンドに表示する最小構成の疎通テストアプリです。

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
2. `http://localhost:8000/api/compress` に `POST` で送信する
3. バックエンドが画像をJPEGとして圧縮する
4. 圧縮後の画像を画面に表示する

## API

```text
POST /api/compress
```

フォームデータ:

- `file`: 画像ファイル

レスポンス:

- `image/jpeg`
