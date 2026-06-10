import asyncio
import configparser
from pathlib import Path
import sys
import time
import uuid

from faker import Faker
import httpx
from loguru import logger

from credentials import generate_credentials


logger.remove()
logger.add(
    sys.stdout, format="[{time:HH:mm:ss.SSS}] {message}", colorize=False)
logger.add("./logs/V2.log", format="[{time:HH:mm:ss.SSS}] {message}")

fake = Faker()

BASE_URL = "https://lvl2.cupflag.top"
BASE_TOKEN = fake.sha256()
DEFAULT_RETRY_AFTER_MS = 10000
MAX_CONCURRENT_WORKERS = 5
CAPTURED_FLAGS = set()


def get_proxy() -> str | None:
    try:
        config = configparser.ConfigParser()
        config_path = Path(__file__).parent / 'proxy.ini'
        config.read(str(config_path))

        username = config['proxy']['username']
        password = config['proxy']['password']
        ip = config['proxy']['ip']
        port = config['proxy']['port']
        proxy = f"http://{username}:{password}@{ip}:{port}"
        return proxy
    except Exception as e:
        logger.error(f"Error reading proxy configuration: {e}")
        return None


async def authorization(client: httpx.AsyncClient, worker_id: int) -> bool:
    main_url = "https://lvl2.cupflag.top"
    headers = {
        "Host": "lvl2.cupflag.top",
        "Connection": "keep-alive",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
        "sec-ch-ua": '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-User": "?1",
        "Sec-Fetch-Dest": "document",
        "Referer": "https://lvl2.cupflag.top/login",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "en",
    }

    try:
        logger.info(f"Worker {worker_id}: GET {main_url}")
        await client.get(main_url, headers=headers, follow_redirects=True)

        login_url = "https://lvl2.cupflag.top/login"
        logger.info(f"Worker {worker_id}: GET {login_url}")
        await client.get(login_url, headers=headers, follow_redirects=True)

        login, password = generate_credentials()
        post = {
            "login": login,
            "password": password
        }
        headers = {
            "Host": "lvl2.cupflag.top",
            "Connection": "keep-alive",
            "Cache-Control": "max-age=0",
            "sec-ch-ua": '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "Origin": "https://lvl2.cupflag.top",
            "Content-Type": "application/x-www-form-urlencoded",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-User": "?1",
            "Sec-Fetch-Dest": "document",
            "Referer": "https://lvl2.cupflag.top/login",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "en",
        }

        logger.info(
            f"Worker {worker_id}: login: user={login} pass=md5(\"{login}\")")

        response = await client.post(login_url, headers=headers, data=post, follow_redirects=True)
        logger.info(
            f"Worker {worker_id}: POST {login_url} → {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Worker {worker_id}: Error: {e}")
        return False


async def catch_cupflags(client: httpx.AsyncClient, worker_id: int) -> int:
    request_id = str(uuid.uuid4())

    headers = {
        "Host": "lvl2.cupflag.top",
        "Connection": "keep-alive",
        "X-Request-Id": request_id,
        "sec-ch-ua-platform": '"Windows"',
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
        "Content-Type": "application/json",
        "sec-ch-ua-mobile": "?0",
        "Accept": "*/*",
        "Origin": "https://lvl2.cupflag.top",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
        "Referer": "https://lvl2.cupflag.top/",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "en",
    }

    body = {"captcha_token": BASE_TOKEN}
    retry_after_ms = DEFAULT_RETRY_AFTER_MS
    try:
        response = await client.post(
            "https://lvl2.cupflag.top/v1/capture",
            headers=headers,
            json=body,
            follow_redirects=True,
            timeout=15.0
        )
        data = response.json()
        logger.info(f"Worker {worker_id}: POST /v1/capture → {data}")

        status = data.get("status")
        if status == "unauthorized":
            return -1

        if status != "ok":
            retry_after_ms = data.get("retry_after_ms", DEFAULT_RETRY_AFTER_MS)
            if not isinstance(retry_after_ms, int):
                retry_after_ms = DEFAULT_RETRY_AFTER_MS
            return retry_after_ms

        flag = data.get("flag")
        if flag and flag not in CAPTURED_FLAGS:
            CAPTURED_FLAGS.add(flag)
            logger.success(
                f"Worker {worker_id}: ✓ Flag #{len(CAPTURED_FLAGS)} captured")

        return retry_after_ms
    except Exception as e:
        logger.exception(f"Worker {worker_id}: Error during capture: {e}")
        return retry_after_ms


async def worker(worker_id: int) -> None:
    await asyncio.sleep(worker_id * (DEFAULT_RETRY_AFTER_MS / MAX_CONCURRENT_WORKERS / 1000))

    logger.info(f"Worker {worker_id} starting")
    logger.info(f"Worker {worker_id}: Connecting to {BASE_URL}")

    async with httpx.AsyncClient(
        verify=False,
        timeout=15.0,
        proxy=get_proxy()
    ) as client:
        while True:
            auth_success = False
            for _ in range(3):
                if await authorization(client, worker_id):
                    auth_success = True
                    break
                await asyncio.sleep(1)

            if not auth_success:
                logger.error(
                    f"Worker {worker_id}: authorization failed after 3 attempts")
                return
            
            while True:
                delay = await catch_cupflags(client, worker_id)
                if delay == -1:
                    break
                await asyncio.sleep(delay / 1000)


async def stats_reporter() -> None:
    start_time = time.monotonic()
    while True:
        await asyncio.sleep(120)
        uptime_seconds = int(time.monotonic() - start_time)
        logger.info(f"Total: {len(CAPTURED_FLAGS)} in {uptime_seconds} s")


async def run_lvl2() -> None:
    tasks = []

    stats_task = asyncio.create_task(stats_reporter())

    for i in range(MAX_CONCURRENT_WORKERS):
        tasks.append(asyncio.create_task(worker(worker_id=i)))

    try:
        await asyncio.gather(*tasks)
    finally:
        stats_task.cancel()

if __name__ == "__main__":
    try:
        asyncio.run(run_lvl2())
    except KeyboardInterrupt:
        logger.info(f"Total: {len(CAPTURED_FLAGS)} unique flags captured")
        logger.warning("Script stopped by user")
