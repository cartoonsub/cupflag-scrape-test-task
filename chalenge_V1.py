import sys
import hashlib
import configparser
from pathlib import Path

import asyncio
import httpx
from faker import Faker
from loguru import logger

logger.remove()
logger.add(
    sys.stdout, format="[{time:HH:mm:ss.SSS}] {message}", colorize=False)
logger.add("./logs/V1.log", format="[{time:HH:mm:ss.SSS}] {message}")

fake = Faker()

BASE_URL = "https://lvl1.cupflag.top"
MAX_CONCURRENT_WORKERS = 5
MAX_ERRORS_BEFORE_STOP = 15


def generate_credentials() -> tuple[str, str]:
    username = fake.user_name()[3:32]
    password = hashlib.md5(username.lower().encode()).hexdigest()
    return username, password


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


async def authorization(client: httpx.AsyncClient) -> bool:
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
        logger.info(f"GET {main_url}")
        await client.get(main_url, headers=headers, follow_redirects=True)

        login_url = "https://lvl1.cupflag.top/login"
        logger.info(f"GET {login_url}")
        await client.get(login_url, headers=headers, follow_redirects=True)

        login, password = generate_credentials()
        post = {
            "login": login,
            "password": password
        }

        logger.info(f"login: user={login} pass=md5(\"{login}\")")
        logger.info(f"POST {login_url}")

        response = await client.post(login_url, headers=headers, data=post, follow_redirects=True)
        logger.info(f"status code: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Error: {e}")
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
            if status != "ok":
                logger.info(f"POST /v1/capture → {data}")
                continue

            flag = data.get("flag")
            logger.info(f"POST /v1/capture → {data}")
            logger.success(f"✓ Flag captured: {flag}")
        except Exception as e:
            error_count += 1
            logger.error(
                f"Worker {worker_id}: Error during catchCupflags: {e} (error count: {error_count})")


async def worker(worker_id: int) -> None:
    logger.info(f"Worker {worker_id} starting")
    logger.info(f"Connecting to {BASE_URL}")

    async with httpx.AsyncClient(verify=False, proxy=get_proxy()) as client:
        while True:
            auth_success = False
            for _ in range(3):
                if await authorization(client):
                    auth_success = True
                    break
                await asyncio.sleep(1)

            if not auth_success:
                logger.error(
                    f"Worker {worker_id}: authorization failed after 3 attempts")
                return

            await catch_cupflags(client, worker_id)


async def run_lvl1() -> None:
    tasks = []
    for i in range(MAX_CONCURRENT_WORKERS):
        tasks.append(asyncio.create_task(
            worker(worker_id=i)))

    await asyncio.gather(*tasks)

if __name__ == "__main__":
    try:
        asyncio.run(run_lvl1())
    except KeyboardInterrupt:
        logger.warning("Скрипт остановлен пользователем")
