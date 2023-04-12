import re
import time
from typing import Any
import requests
from dataclasses import dataclass
from loguru import logger


def count_doown(seconds: int):
    for i in range(seconds, 0, -1):
        print(f"\r{i} seconds left to start downloading ", end="")
        time.sleep(1)
    print()


class MakeOptional:
    def __init__(self: Any, **kwargs):
        for k in self.__dataclass_fields__:
            setattr(self, k, None)

        for k, v in kwargs.items():
            setattr(self, k, v)


@dataclass
class User:
    username: str
    password: str


@dataclass(init=False)
class VideoRes(MakeOptional):
    VID: str
    heb: str
    eng: str
    description: str
    addDate: str
    viewnumber: str
    watch: dict[str, str]
    error: str


@dataclass
class SearchSeriesResult:
    name: str
    id: str


class SdarotTV:
    def __init__(self, user: User = None, host: str = "https://sdarot.tv", cookie: str = None):
        self.host = host
        if cookie:
            logger.info("\rUsing provided cookie to skip login")
            self.cookie = cookie
            return

        indexRes = self.request("/")
        self.cookie = indexRes.headers.get("set-cookie")

        if user is not None:
            self.login(user)
        else:
            logger.warning("\rNo user was provided. as for 12/04/2023 sdarot.tv requires login to download videos. We will try to download the videos anyway but it might fail.")


    def login(self, user: User):
        res = self.request("/login", {
            "body": f"location=%2F&username={user.username}&password={user.password}&submit_login=",
            "method": "POST"
        })

        if "שם המשתמש ו/או הסיסמה שהזנת שגויים!" in res.text:
            raise Exception("Wrong username or password")
        if "לא הזנת פרטי התחברות!" in res.text:
            raise Exception("Missing username or password")
        if "ניצלת את כל נסיונות ההתחברות העומדים לרשותך. נא נסה שנית מאוחר יותר." in res.text:
            raise Exception("Too many unsuccessful login attempts. Please try again later.")


    def request(self, url: str, options=None):
        headers = {
            "accept": "*/*",
            "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Referer": self.host,
            **(options.get("headers") if options and options.get("headers") else {})
        }
        if getattr(self, "cookie", None):
            headers["cookie"] = self.cookie
        response = requests.request(
            method=options["method"] if options and options.get("method") else "GET",
            url=f"{self.host}{url}",
            headers=headers,
            data=options["body"] if options and options.get("body") else None
        )
        return response

    def searchSeries(self, name: str) -> str | None:
        response = self.request(f"/ajax/index?search={name}")
        res = [SearchSeriesResult(**r) for r in response.json()]
        logger.info(f"\rFound {len(res)} series matching {name} - {[r.name for r in res]}")
        if len(res) > 0:
            return res[0].id
        return None

    def downloadVideoById(self, seriesId: str, season: int, episode: int):
        def get_token():
            tokenRes = self.request("/ajax/watch", {
                "body": f"preWatch=true&SID={seriesId}&season={season}&ep={episode}",
                "method": "POST"
            })
            return tokenRes.text


        def get_video_res():
            finalRes = self.request("/ajax/watch", {
                "body": f"watch=true&token={token}&serie={seriesId}&season={season}&episode={episode}&type=episode",
                "method": "POST"
            })

            return VideoRes(**finalRes.json())

        token = get_token()
        res = get_video_res()

        if re.fullmatch(r"עליך להמתין \d+ שניות", res.error):
            count_doown(30)
            res = get_video_res()

        if res.error:
            raise Exception(res.error if res.error else "Unknown error")
        if not res.watch:
            raise Exception("No videos found for this episode")

        highest_res = max(res.watch.keys(), key=int)
        video_path = f"video-{res.VID}.mp4"
        video_url = f"https:{res.watch[highest_res]}"

        with requests.get(video_url, headers={"accept": "*/*", "cookie": self.cookie}, stream=True) as response:
            response.raise_for_status()

            total_size = int(response.headers.get('Content-Length', 0))
            bytes_so_far = 0

            with open(video_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    bytes_so_far += len(chunk)
                    progress = round(bytes_so_far / total_size * 100, 2)
                    print(f"\rDownloaded {bytes_so_far} / {total_size} bytes ({progress}%)", end="")
                print()
                logger.success(f"\rDownloaded {video_path}")


    def downloadVideo(self, name: str, season: int, episode: int):
        seriesId = self.searchSeries(name)
        if seriesId:
            self.downloadVideoById(seriesId, season, episode)
        else:
            raise Exception("Series not found")


def main():
    user = User("YOUR_USERNAME", "YOUR_PASSWORD")  # credintials for sdarot.tv
    sdarot = SdarotTV(user=user, host="https://sdarot.buzz")
    sdarot.downloadVideo("the simpsons", 1, 1)


if __name__ == '__main__':
    main()
