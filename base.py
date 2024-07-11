import os
import sys
import json
from typing import Optional
from loguru import logger
from config import load_config
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.server_api import ServerApi
from concurrent.futures import ThreadPoolExecutor


load_dotenv()


class VerifyException(Exception):
    def __init__(self, message=None):
        self.message = message


class Base:
    config = load_config()
    mongo_url = os.getenv("MONGO_URL")
    mongo_client = AsyncIOMotorClient(host=mongo_url, server_api=ServerApi("1"))
    proxy = os.getenv("PROXY") or os.getenv("HTTP_PROXY") or None
    proxies = {"http": proxy, "https": proxy}
    executor = ThreadPoolExecutor(max_workers=1)

    def __init__(self):
        logger.add(
            sys.stdout,
            colorize=True,
            format="<green>{time:YYYY-MM-DD at HH:mm:ss}</green> | <level>{message}</level>",
        )
        logger.add(
            "out.log",
            retention="1 days",
            enqueue=True,
            backtrace=True,
            diagnose=True,
        )
        if os.environ.get("CI"):
            self.config.llm_check = False
            self.config.query_token = False
            self.config.always_token = False

    def check_block_list(self, data: dict) -> Optional[str]:
        """检查字典中的值是否在相应的块列表中"""
        for key, value in data.items():
            if value:
                if hasattr(value, "lower"):
                    value = value.lower()
                block_list = getattr(self.config, key + "_block_list", [])
                for item in block_list:
                    if item in value:
                        print(
                            json.dumps(
                                {"检查字段": key, "字段": value, "包含": item},
                                ensure_ascii=False,
                                indent=4,
                            )
                        )
                        return key
        return None

    @logger.catch
    def handle_exception(self, exception):
        raise exception
