import asyncio
import configparser
import sys
import time
from pathlib import Path

import httpx
from loguru import logger

from credentials import generate_credentials

logger.remove()
logger.add(
    sys.stdout, format="[{time:HH:mm:ss.SSS}] {message}", colorize=False)
logger.add("./logs/V1.log", format="[{time:HH:mm:ss.SSS}] {message}")

BASE_URL = "https://lvl1.cupflag.top"
MAX_CONCURRENT_WORKERS = 5
MAX_ERRORS_BEFORE_STOP = 15
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
    main_url = "https://lvl1.cupflag.top/"
    headers = {
        "Host": "lvl1.cupflag.top",
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
        "Referer": "https://lvl1.cupflag.top/login",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "en",
    }

    try:
        logger.info(f"Worker {worker_id}: GET {main_url}")
        await client.get(main_url, headers=headers, follow_redirects=True)

        login_url = "https://lvl1.cupflag.top/login"
        logger.info(f"Worker {worker_id}: GET {login_url}")
        await client.get(login_url, headers=headers, follow_redirects=True)

        login, password = generate_credentials()
        post = {
            "login": login,
            "password": password
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


async def catch_cupflags(client: httpx.AsyncClient, worker_id: int) -> None:
    headers = {
        "Host": "lvl1.cupflag.top",
        "Connection": "keep-alive",
        "sec-ch-ua-platform": '"Windows"',
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
        "Content-Type": "application/json",
        "sec-ch-ua-mobile": "?0",
        "Accept": "*/*",
        "Origin": "https://lvl1.cupflag.top",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
        "Referer": "https://lvl1.cupflag.top/",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "en",
    }

    error_count = 0
    capture_url = f"{BASE_URL}/v1/capture"

    while True:
        if error_count >= MAX_ERRORS_BEFORE_STOP:
            logger.warning(
                f"Worker {worker_id}: Too many errors, stopping catchCupflags")
            break

        try:
            await asyncio.sleep(0.1)
            response = await client.post(capture_url, headers=headers, json={}, follow_redirects=True)
            data = response.json()
            status = data.get("status")
            if status == "unauthorized":
                break

            logger.info(f"Worker {worker_id}: POST /v1/capture → {data}")
            if status != "ok":
                continue

            flag = data.get("flag")
            if flag and flag not in CAPTURED_FLAGS:
                CAPTURED_FLAGS.add(flag)
                logger.success(
                    f"Worker {worker_id}: ✓ Flag #{len(CAPTURED_FLAGS)} captured")
        except Exception as e:
            error_count += 1
            logger.error(
                f"Worker {worker_id}: Error during catchCupflags: {e} (error count: {error_count})")


async def worker(worker_id: int) -> None:
    logger.info(f"Worker {worker_id} starting")
    logger.info(f"Worker {worker_id}: Connecting to {BASE_URL}")

    async with httpx.AsyncClient(verify=False, proxy=get_proxy()) as client:
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

            await catch_cupflags(client, worker_id)


async def stats_reporter() -> None:
    start_time = time.monotonic()
    while True:
        await asyncio.sleep(120)
        uptime_seconds = int(time.monotonic() - start_time)
        logger.info(f"Total: {len(CAPTURED_FLAGS)} in {uptime_seconds} s")


async def run_lvl1() -> None:
    tasks = []

    stats_task = asyncio.create_task(stats_reporter())

    for i in range(MAX_CONCURRENT_WORKERS):
        tasks.append(asyncio.create_task(
            worker(worker_id=i)))

    try:
        await asyncio.gather(*tasks)
    finally:
        stats_task.cancel()

if __name__ == "__main__":
    try:
        asyncio.run(run_lvl1())
    except KeyboardInterrupt:
        logger.info(f"Total: {len(CAPTURED_FLAGS)} unique flags captured")
        logger.warning("Script stopped by user")
