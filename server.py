import asyncio
import logging
import os
import re
import click
import uvicorn
from fastapi import BackgroundTasks, FastAPI
from fastapi.responses import FileResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from loguru import logger
from pydantic import BaseModel
from uvicorn import Config
from main import HOST, SdarotTV, User


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
        return {"error": str(e) or "Failed to login to sdarot.tv"}


@app.post("/search")
def search(data: SearchData):
    try:
        sdarot = SdarotTV(cookie=data.cookie)
        matched_sires = sdarot.search_series(data.name)
        return matched_sires
    except Exception as e:
        logger.error(e)
        return []


@app.post("/download")
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


async def serve(self, sockets=None, shared_value=None):
    uvicorn_logger = logging.getLogger("uvicorn.error")
    process_id = os.getpid()

    config = self.config
    if not config.loaded:
        config.load()

    self.lifespan = config.lifespan_class(config)

    self.install_signal_handlers()

    message = "Started server process [%d]"
    color_message = "Started server process [" + click.style("%d", fg="cyan") + "]"
    uvicorn_logger.info(message, process_id, extra={"color_message": color_message})

    await self.startup(sockets=sockets)
    if shared_value:
        shared_value.value = True

    if self.should_exit:
        return
    await self.main_loop()
    await self.shutdown(sockets=sockets)

    message = "Finished server process [%d]"
    color_message = "Finished server process [" + click.style("%d", fg="cyan") + "]"
    uvicorn_logger.info(message, process_id, extra={"color_message": color_message})


def main(port=8000, shared_value=None):
    async def start_server():
        app.mount("/", StaticFiles(directory="./static", html=True), name="static")
        server = uvicorn.Server(config=Config(app, host="0.0.0.0", port=port))
        await serve(server, shared_value=shared_value)

    asyncio.run(start_server())


if __name__ == '__main__':
    main()
