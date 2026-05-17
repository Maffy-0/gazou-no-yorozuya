from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# 作成したルーターをインポート
from app.api.compress import router as compress_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 窓口（ルーター）を登録する
app.include_router(compress_router)

@app.get("/")
def read_root():
    return {"message": "Hello, FastAPI is running!"}
