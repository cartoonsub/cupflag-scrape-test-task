import asyncio
import hashlib
import sys
import uuid
import configparser
from pathlib import Path

from loguru import logger
from faker import Faker
import httpx


logger.remove()
logger.add(
    sys.stdout, format="[{time:HH:mm:ss.SSS}] {message}", colorize=False)
logger.add("./logs/V2.log", format="[{time:HH:mm:ss.SSS}] {message}")

fake = Faker()

BASE_URL = "https://lvl2.cupflag.top"
BASE_TOKEN = "1.y782XzQ1bGAC5pzCV8ICbJNCo6nK6Mq1PTqZxHHdZNa3avCXyhW54orMfVNR1zyVJe49JR1bKMfCj-fEB2AAncebL-l7WPWz3uxPVVWZlyI-HktOueMyigx6bKTGVQdLc2Do34duw16nrAaWLaIDhLL-YW5Wf6YQ4k1ncDQmzH-mt1BHU1G2YOz_DQA0IiyOFn8PvJcTOZhnrBE_riNLWHwjcgpM5o8yc5AUcYoar3I_j9YbdZgpoWBs_fkiESXDOKyitNcRsN62b0g9mU3SE-9Ub35fQvxEuaaQ2_Rbk0-Zp8y1THeyOcfpJv_3g2Xlt4glJiXAMARB2MhxWysRbN3lm_Sb_1EtVHc5g__A3TVkNZbH39aL_sG2ItZRv819oVxYBOYeZeggEE9XXb5qXgov4kJ2tciCLfRae0K4gFIIsrNoqhkfCfnvWF8VL_iwQaavccWDcPh8OuEkfH9E7VjnYSsxnvIHzRrd7KHVQOVni-DXofBnWRfnhvollYspKdbG3iUU8hIF-Vb8_p6MPFrqTVVGMFfqYoj5MYZjUvOFJgw-GT29rZPxHkT4kzEH1tth4Uk3p7QV2EAe882WALAzrbzlP545pPda-YsGtO1pmhwi6UO3L4DT7WoRjITNvzmJ_0GRt2t3nd08yJVoIu2UIxgmRbxb8zt27FRilX-QcAtRU5gZj9wn35CyGAr0.Xou71KxukLyU8UAvQFujoA.8618abeaf1db537d96c31b2c72d15367e79e24d2d375d9aadec7dc997889dd38"
DEFAULT_RETRY_AFTER_MS = 10000


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


async def set_token() -> None:
    # cf-chl-widget-ldxe3_response
    # не возвращать каждый раз, т.к. он не меняется
    # BASE_TOKEN = and get from browser
    pass


async def authorization(client: httpx.AsyncClient) -> bool:
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
        logger.info(f"GET {main_url}")
        await client.get(main_url, headers=headers, follow_redirects=True)

        login_url = "https://lvl2.cupflag.top/login"
        logger.info(f"GET {login_url}")
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

        logger.info(f"login: user={login} pass=md5(\"{login}\")")
        logger.info(f"POST {login_url}")

        response = await client.post(login_url, headers=headers, data=post, follow_redirects=True)
        logger.info(f"status code: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Error: {e}")
        return False


async def catch_cupflags(client: httpx.AsyncClient) -> int:
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
        response = await client.post("https://lvl2.cupflag.top/v1/capture", headers=headers, json=body, follow_redirects=True)
        data = response.json()
        status = data.get("status")
        if status != "ok":
            logger.info(f"POST /v1/capture → {data}")
            retry_after_ms = data.get("retry_after_ms", DEFAULT_RETRY_AFTER_MS)
            if not isinstance(retry_after_ms, int):
                retry_after_ms = DEFAULT_RETRY_AFTER_MS
            logger.warning(
                f"Capture failed, retrying after {retry_after_ms} ms")
            return retry_after_ms

        flag = data.get("flag")
        logger.info(f"POST /v1/capture → {data}")
        logger.success(f"✓ Flag captured: {flag}")
        return retry_after_ms
    except Exception as e:
        logger.error(f"Error capturing flag: {e}")
        return retry_after_ms


async def run_lvl2() -> None:
    # background_tasks = set()
    async with httpx.AsyncClient(
        verify=False,
        timeout=10.0,
        proxy=get_proxy()
        ) as client:
        if not await authorization(client):
            logger.critical("Authorization failed. Stopping.")
            return

        while True:
            delay = await catch_cupflags(client)
            await asyncio.sleep(delay / 1000)
        # while True:
        #     task = asyncio.create_task(catch_cupflags(client))
        #     background_tasks.add(task)
        #     task.add_done_callback(background_tasks.discard)
        #     await asyncio.sleep(RETRY_AFTER_MS / 1000)

if __name__ == "__main__":
    try:
        asyncio.run(run_lvl2())
    except KeyboardInterrupt:
        logger.warning("Скрипт остановлен пользователем")
