# -*- coding: utf-8 -*-

from __future__ import annotations
from abc import ABC, abstractmethod
import random
import string

import pytz
import datetime
import os, argparse
import platform
import asyncio, shlex
from os.path import join
from aiofiles.os import remove
from aiohttp import ClientSession
from typing import Union, List
from logging import getLogger, FileHandler, StreamHandler, INFO, basicConfig

import yt_dlp

__version__ = "1.0"
__author__ = "https://t.me/Reason_Someone"
__license__ = "MIT"
__copyright__ = "Copyright 2024"


basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[FileHandler("logs.txt", encoding="utf-8"), StreamHandler()],
    level=INFO,
)

LOGGER = getLogger("drm")

os.makedirs("Videos/", exist_ok=True)


class SERVICE(ABC):

    def __init__(self):
        self._remoteapi = "https://app.magmail.eu.org/get_keys"

    @staticmethod
    def c_name(name: str) -> str:
        for i in ["/", ":", "{", "}", "|"]:
            name = name.replace(i, "_")
        return name

    def get_date(self) -> str:
        tz = pytz.timezone("Asia/Kolkata")
        ct = datetime.datetime.now(tz)
        return ct.strftime("%d-%m-%Y %H-%M-%S")

    async def get_keys(self):
        async with ClientSession(headers={"user-agent": "okhttp"}) as session:
            async with session.post(
                self._remoteapi, json={"link": self.mpd_link}
            ) as resp:
                if resp.status != 200:
                    raise Exception(f"Failed to get keys: {await resp.text()}")
                response = await resp.json(content_type=None)
        self.mpd_link = response["MPD"]
        return response["KEY_STRING"]

    def get_mp4decrypt(self):
        macos = "binary/macos/mp4decrypt"
        linux = "binary/linux/mp4decrypt"
        windows = "binary/windows/mp4decrypt.exe"
        if platform.system() == "Darwin":
            return macos
        elif platform.system() == "Linux":
            return linux
        elif platform.system() == "Windows":
            return windows


class Download(SERVICE):

    def __init__(self, name: str, resl: str, mpd: str, ext: str):
        super().__init__()
        self.mpd_link = mpd
        self.name = self.c_name(name)
        self.ext = ext
        self.vid_format = self.get_quality(resl, mpd)
        self.random_string = self.random_string_gen().upper()
        self.videos_dir = f"Videos/{self.random_string}"
        self.merged = join(self.videos_dir, f"{self.name}.{self.ext}")
        self.make_dirs()

    def make_dirs(self):
        os.makedirs(self.videos_dir, exist_ok=True)

    def random_string_gen(self):
        return "".join(random.choices(string.ascii_letters + string.digits, k=12))

    async def process_non_drm_video(self):
        LOGGER.info(f"Downloading Started...")
        if await self.__yt_dlp_drm():
            LOGGER.info(f"Downloading complete for: {self.name}")
            return self.merged
        LOGGER.error(f"Processing failed for: {self.name}")
        return None

    async def process_video(self):
        key = await self.get_keys()
        if not key:
            raise Exception("Failed to get keys")

        LOGGER.info(f"MPD: {self.mpd_link}")
        LOGGER.info(f"Got the Keys > {key}")
        LOGGER.info(f"Downloading Started...")
        if await self.__yt_dlp_drm() and await self.__decrypt(key):
            LOGGER.info(f"Downloading complete for: {self.name}")
            return self.merged
        LOGGER.error(f"Processing failed for: {self.name}")
        return None

    async def __subprocess_call(self, cmd: Union[str, List[str]]):
        if isinstance(cmd, str):
            cmd = shlex.split(cmd)
        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        if process.returncode != 0:
            LOGGER.error(f"Command failed: {' '.join(cmd)}\nError: {stderr.decode()}")
            return False
        return True

    async def __yt_dlp_drm(self) -> bool:
        LOGGER.info(f"Quality: {self.vid_format}")

        video_command = f'yt-dlp --no-check-certificates --no-warnings --merge-output-format mp4 -f "{self.vid_format}" -o "{self.merged}" -N 50 --retries 100 --fragment-retries 100 --external-downloader aria2c --downloader-args "aria2c: -x 16 -j 32" "{self.mpd_link}"'

        for i in range(3):
            try:
                LOGGER.info(f"Downloading video with command: {video_command}")
                video_download = await self.__subprocess_call(video_command)
                if not video_download:
                    LOGGER.error("Video download failed")
                    raise Exception("Failed to dl video")

                return True
            except Exception as e:
                LOGGER.error(f"Failed to download video and audio: {str(e)}")
                continue

        raise Exception("Failed to download video and audio")

    async def __decrypt(self, key: str):
        LOGGER.info("Decrypting...")
        mp4decrypt = self.get_mp4decrypt()
        video_decrypt = self.__subprocess_call(
            f'{mp4decrypt} --show-progress {key} "{self.merged}" "{self.merged}"'
        )
        return await asyncio.gather(video_decrypt)

    async def normal_download(self):
        url = self.mpd_link
        async with ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:

                    if not os.path.exists(self.videos_dir):
                        os.makedirs(self.videos_dir)

                    # check if name has an extension
                    if "." in self.name:
                        ext = self.name.split(".")[-1]
                    else:
                        ext = url.split("?")[0].split("/")[-1].split(".")[-1]

                    file_path = os.path.join(self.videos_dir, f"{self.name}.{ext}")
                    with open(file_path, "wb") as f:
                        while True:
                            chunk = await response.content.read(1024)
                            if not chunk:
                                break
                            f.write(chunk)
                    return file_path
                else:
                    # Handle non-200 responses
                    return None

    def is_ytdlp_supported(self, url):
        extractors = yt_dlp.extractor.gen_extractors()
        for e in extractors:
            if e.suitable(url) and e.IE_NAME != "generic":
                return True
        return False

    def get_quality(self, quality, url=None):
        if quality == "1":
            ytf = "1080"
        elif quality == "2":
            ytf = "480"
        elif quality == "3":  # lowest
            ytf = "360"

        if "youtu" in url:
            #ytf = f"b[height<={ytf}][ext=mp4]/bv[height<={ytf}][ext=mp4]+ba[ext=m4a]/b[ext=mp4]"
            ytf = f"bestvideo[height<={ytf}][ext=mp4]+bestaudio[ext=m4a]/best[height<={ytf}][ext=mp4]"
        else:
            ytf = f"b[height<={ytf}]/bv[height<={ytf}]+ba/b/bv+ba"
        
        return ytf


async def download_main(name, resl, mpd, drm_ext="mkv"):
    downloader = Download(name, resl, mpd, drm_ext)
    exts = [".m3u8", ".mp4", ".webm", ".mkv", ".flv", ".avi", ".mov", ".wmv", ".mpd"]
    excluded = [
        ".pdf",
        ".exe",
        ".zip",
        ".rar",
        ".apk",
        ".torrent",
        ".iso",
        "drive.google.com",
    ]

    if "cpvod.testbook.com" in mpd:
        print("DRM video")

        try:
            await downloader.process_video()
            return downloader.merged, True
        except Exception as e:
            print(f"Error: {str(e)}")
            return await downloader.process_non_drm_video(), True

    elif any(ext in mpd for ext in exts) and not any(ext in mpd for ext in excluded):
        print("Non-drm video")
        return await downloader.process_non_drm_video(), True
    elif downloader.is_ytdlp_supported(mpd) and not any(ext in mpd for ext in excluded):
        print("Ytdlp supported")
        return await downloader.process_non_drm_video(), True
    else:
        print("Normal download")
        return await downloader.normal_download(), False
