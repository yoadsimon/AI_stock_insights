import os
import logging
import random
import time
from playwright.async_api import async_playwright
from common.inputs.video_map import VIDEO_DESCRIPTION_MAP
from dotenv import load_dotenv

load_dotenv()

browsers_path = os.getenv('PLAYWRIGHT_BROWSERS_PATH', '/home/airflow/.cache/ms-playwright')
chromium_versions = [d for d in os.listdir(browsers_path) if d.startswith('chromium-')]
if not chromium_versions:
    raise Exception(f"No Chromium versions found in {browsers_path}")
chromium_version = chromium_versions[0]
executable_path = os.path.join(browsers_path, chromium_version, 'chrome-linux', 'chrome')
if not os.path.exists(executable_path):
    raise FileNotFoundError(f"Chromium executable not found at {executable_path}")


async def open_finance_yahoo(p):
    base_url = "https://finance.yahoo.com/"
    browser = await p.chromium.launch(headless=True,
                                      # executable_path=executable_path,
                                      )
    page = await browser.new_page()
    await page.goto(base_url)
    await page.wait_for_timeout(10000)
    try:
        time.sleep(0.2)
        await page.click("button#scroll-down-btn")
        await page.click("button.btn.secondary.reject-all")
    except Exception:
        pass
    return browser, page


async def get_text_from_url(url, page):
    try:
        await page.goto(url)
        await page.wait_for_timeout(10000)
        body_handle = await page.query_selector("body")
        if body_handle:
            text_raw = await page.evaluate("document.body.innerText")
        else:
            text_raw = "Error: Body element is not present on the page."
        return text_raw
    except Exception as e:
        print(f"Error fetching text from URL {url}: {e}")
        return None


async def get_text_by_url(urls):
    text_by_link = {}
    time.sleep(0.2)
    async with async_playwright() as p:
        browser, page = await open_finance_yahoo(p)
        if not browser or not page:
            print("Failed to open browser or page.")
            return text_by_link
        try:
            for url in urls:
                text = await get_text_from_url(url, page)
                text_by_link[url] = text
            return text_by_link
        finally:
            await browser.close()


def save_to_temp_file(text, name):
    if not os.path.exists('temp'):
        os.makedirs('temp')
    with open(f'temp/{name}.txt', 'w', encoding='utf-8') as file:
        file.write(text)


def read_temp_file(file_name):
    if not file_name:
        return None
    if 'temp/' not in file_name:
        file_path = f"temp/{file_name}.txt"

    if "common/" not in file_path:
        file_path = f"common/{file_path}"

    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            content = file.read()
        return content

    return None


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    pass


def fix_video_name(name):
    if not name.endswith(".mp4"):
        name += ".mp4"
    if name not in VIDEO_DESCRIPTION_MAP.keys():
        name = None
    if not name:
        return random.choice(["Interactive_Trading_Screen.mp4", "Stock_Ticker_Grid.mp4"])
    return name

if __name__ == '__main__':
    fix_video_name(name="Market_Downturn_Graph.mp4")
# async def test_playwright():
#     async with async_playwright() as p:
#         browser = await p.chromium.launch(headless=True)
#         page = await browser.new_page()
#         await page.goto('https://playwright.dev')
#         # returns text form the page
#         print(await page.title())
#         await browser.close()
#     print("Test completed")
