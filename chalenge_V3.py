from pathlib import Path
import configparser
import sys
import hashlib

import asyncio
from camoufox.async_api import AsyncCamoufox
from browserforge.fingerprints import Screen

from faker import Faker
from loguru import logger

logger.remove()
logger.add(
    sys.stdout, format="[{time:HH:mm:ss.SSS}] {message}", colorize=False)
logger.add("./logs/V3.log", format="[{time:HH:mm:ss.SSS}] {message}")


fake = Faker()


def generate_credentials() -> tuple[str, str]:
    username = fake.user_name()[3:32]
    password = hashlib.md5(username.lower().encode()).hexdigest()
    return username, password


class CupflagWorker:
    def __init__(self):
        self.proxy = None
        self.set_proxy()
        self.base_url = "https://lvl3.cupflag.top"

        constrains = Screen(max_width=1280, max_height=631)
        profile_path = Path(__file__).parent / 'data' / 'cupflag_profile'

        self.camoufox_context = AsyncCamoufox(
            headless=True,
            geoip=True,
            proxy=self.proxy,
            screen=constrains,
            persistent_context=True,
            user_data_dir=profile_path
        )
        self.page = None
        logger.info("Browser initialized")

    def set_proxy(self) -> None:
        try:
            config = configparser.ConfigParser()
            config_path = Path(__file__).parent / 'proxy.ini'
            config.read(str(config_path))

            username = config['proxy']['username']
            password = config['proxy']['password']
            ip = config['proxy']['ip']
            port = config['proxy']['port']

            self.proxy = {
                'server': f"http://{ip}:{port}",
                'username': username,
                'password': password
            }
            logger.info("Proxy configuration loaded successfully.")
        except Exception as e:
            logger.error(f"Error reading proxy configuration: {e}")
            self.proxy = None

    async def run(self):
        async with self.camoufox_context as context:
            if context.pages:
                self.page = context.pages[0]
            else:
                self.page =await context.new_page()

            await self.page.set_viewport_size({'width': 1280, 'height': 631})

            await self.page.goto(self.base_url, wait_until="domcontentloaded")

            if not await self.authenticate():
                logger.error("Authentication failed, stopping worker.")
                return

            logger.info("Authentication successful.")

            await self.catch_booking_key()

            logger.info("Worker finished.")
            await self.page.wait_for_timeout(1000000)  # todo remove

    async def authenticate(self) -> bool:
        if await self.check_authentication():
            logger.info("Already authenticated.")
            return True

        username, password = generate_credentials()

        logger.info("Attempting authentication...")
        await self.page.wait_for_timeout(10000)
        try:
            url = 'https://lvl3.cupflag.top/login'
            await self.page.goto(url)
            await self.page.wait_for_selector('input[name="login"]', timeout=10000)

            await self.page.wait_for_timeout(1000)
            await self.page.fill('input[name="login"]', username)
            await self.page.wait_for_timeout(1000)
            await self.page.fill('input[name="password"]', password)
            await self.page.wait_for_timeout(1500)

            await self.page.click("button[type='submit']")

            await self.page.wait_for_timeout(5000)
            if not await self.check_authentication():
                logger.error("Authentication failed after login attempt.")
                return False
            return True
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False

    async def check_authentication(self, check_current_page=False) -> bool:
        logger.info("Checking authentication status...")
        try:
            url = "https://lvl3.cupflag.top/"
            if not check_current_page:
                await self.page.goto(url, wait_until="domcontentloaded", timeout=10000)

            await self.page.wait_for_selector(".container", timeout=30000)
            if await self.page.locator('#capture-btn').count() > 0:
                logger.info("Found capture button, already authenticated.")
                return True

            if await self.page.locator("input[type='password']").count() > 0:
                logger.info("Found password field, not authenticated.")
                return False
            return False
        except Exception as e:
            logger.error(f"Not authenticated: {e}")
            return False

    async def catch_booking_key(self):
        while True:
            await self.click_checkbox()
            await self.clickCaptureButton()
            await self.page.wait_for_timeout(5000)
            try:
                await self.page.wait_for_selector('#queue-token-input', state="attached", timeout=10000)
                booking_key = await self.page.locator('#queue-token-input').input_value()
                print(f"Booking key: {booking_key}")
            except Exception as e:
                print(f"Error waiting for booking key: {e}")

    async def click_checkbox(self):
        try:
            for _ in range(10):
                await self.page.wait_for_selector('#capture-btn', timeout=10000)
                is_disabled =await self.page.locator('#capture-btn').is_disabled()
                if not is_disabled:
                    logger.info(
                        "Capture button is enabled, no need to click checkbox.")
                    return

                logger.info(
                    "Capture button is disabled, attempting to click checkbox.")

                container_selector = '#turnstile-container'
                container = self.page.locator(container_selector)
                await container.wait_for(state="visible", timeout=10000)
                box = await container.bounding_box()
                if box:
                    x = box['x'] + 45
                    y = box['y'] + (box['height'] / 2)

                    logger.info(
                        f"Container coordinates: x={box['x']}, y={box['y']}. Clicking...")
                    await self.page.mouse.move(x, y, steps=5)
                    await self.page.wait_for_timeout(200)
                    await self.page.mouse.click(x, y, delay=150)

                    logger.info("Click on coordinates completed!")
                    await self.page.wait_for_timeout(5000)
                else:
                    logger.error(
                        "Не удалось получить bounding_box родительского контейнера.")
        except Exception as e:
            logger.error(f"Error clicking checkbox: {e}")


    async def clickCaptureButton(self):
        try:
            await self.page.wait_for_selector('#capture-btn', timeout=10000)
            is_disabled =await self.page.locator('#capture-btn').is_disabled()
            if is_disabled:
                await self.click_checkbox()
                await self.page.wait_for_timeout(2000)

            await self.page.wait_for_selector('#capture-btn', timeout=10000)
            if await self.page.locator('#capture-btn').is_disabled():
                logger.error(
                    "Capture button is still disabled after clicking checkbox.")
                return

            await self.page.click('#capture-btn')
        except Exception as e:
            print(f"Error clicking capture button: {e}")


async def run_lvl3():
    logger.info("V3 Worker starting")
    worker = CupflagWorker()
    await worker.run()

if __name__ == "__main__":
    try:
        asyncio.run(run_lvl3())
    except KeyboardInterrupt:
        logger.warning("Скрипт остановлен пользователем")
