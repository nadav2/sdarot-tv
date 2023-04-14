import uvicorn
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response, RedirectResponse
from fastapi import FastAPI
from pydantic import BaseModel
import os
from loguru import logger
from main import SdarotTV, User, HOST
import re
from fastapi import BackgroundTasks


class DownloadData(BaseModel):
    cookie: str
    name: str
    season: int
    episode: int
    seriesId: str


class LoginData(BaseModel):
    username: str
    password: str


class SearchData(BaseModel):
    cookie: str
    name: str


app = FastAPI()


@app.post("/login")
def login(data: LoginData, response: Response):
    try:
        user = User(data.username, data.password)
        sdarot = SdarotTV(user=user)
        return {"sdarotTVCookie": sdarot.cookie}
    except Exception as e:
        logger.error(e)
        response.status_code = 500
        return {"error": "Failed to login"}


@app.post("/search")
def search(data: SearchData):
    try:
        sdarot = SdarotTV(cookie=data.cookie)
        matched_sires = sdarot.search_series(data.name)
        return matched_sires
    except Exception as e:
        logger.error(e)
        return []


@app.post("/download", status_code=200)
def download(data: DownloadData, response: Response, background_tasks: BackgroundTasks):
    def escape_file_name(name: str):
        return re.sub(r'[\\/*?:"<>|]', '|', name)
    try:
        sdarot = SdarotTV(cookie=data.cookie)
        file_name = f"./videos/{escape_file_name(f'{data.name}-{data.season}-{data.episode}')}.mp4"
        os.makedirs(os.path.dirname(file_name), exist_ok=True)
        video_path = sdarot.download_video_by_id(data.seriesId, data.season, data.episode, file_name)
        background_tasks.add_task(os.remove, video_path)
        return FileResponse(video_path)
    except Exception as e:
        logger.error(e)
        response.status_code = 500
        return {"error": str(e) or "Failed to download video"}


@app.get("/status")
def status():
    return RedirectResponse(f"{HOST}/status")


app.mount("/", StaticFiles(directory="./static", html=True), name="static")

if __name__ == '__main__':
    uvicorn.run("server:app", host="0.0.0.0", port=8000)
