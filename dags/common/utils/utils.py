import os
import logging
import random
import time
from playwright.async_api import async_playwright
from common.inputs.video_map import VIDEO_DESCRIPTION_MAP
from dotenv import load_dotenv
import boto3
from airflow.hooks.base_hook import BaseHook
import shutil
from common.utils.consts import BUCKET_NAME

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


def get_s3_client(conn_id='aws_default'):
    conn = BaseHook.get_connection(conn_id)
    extra = conn.extra_dejson or {}
    aws_access_key_id = conn.login
    aws_secret_access_key = conn.password
    region_name = extra.get('region_name', 'us-east-1')
    s3_client = boto3.Session(
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name=region_name
    ).client('s3')

    return s3_client


def save_to_s3(file_name, data, file_type='txt'):
    s3_client = get_s3_client()

    s3_client.put_object(Bucket=BUCKET_NAME, Key=f"{file_name}.{file_type}", Body=data)


def read_from_s3(file_name, file_type='txt'):
    s3_client = get_s3_client()
    response = s3_client.get_object(Bucket=BUCKET_NAME, Key=f"{file_name}.{file_type}")
    return response['Body'].read().decode('utf-8')


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


def clean_dir(dir_name):
    if os.path.exists(dir_name) and os.path.isdir(dir_name):
        for entry in os.listdir(dir_name):
            entry_path = os.path.join(dir_name, entry)
            try:
                if entry == "disclaimer_video.mp4":
                    continue
                if os.path.isfile(entry_path) or os.path.islink(entry_path):
                    os.unlink(entry_path)
                elif os.path.isdir(entry_path):
                    shutil.rmtree(entry_path)
            except Exception as e:
                print(f'Failed to delete {entry_path}. Reason: {e}')
        print(f"All contents of the directory '{dir_name}' have been removed, except 'disclaimer_video.mp4'.")
    else:
        print(f"The directory '{dir_name}' does not exist.")

# def save_to_temp_file(text, name):
#     if not os.path.exists('temp'):
#         os.makedirs('temp')
#     with open(f'temp/{name}.txt', 'w', encoding='utf-8') as file:
#         file.write(text)
#
# def read_temp_file(file_name):
#     if not file_name:
#         return None
#     if 'temp/' not in file_name:
#         file_path = f"temp/{file_name}.txt"
#
#     if "common/" not in file_path:
#         file_path = f"common/{file_path}"
#
#     if os.path.exists(file_path):
#         with open(file_path, 'r') as file:
#             content = file.read()
#         return content
#
#     return None
