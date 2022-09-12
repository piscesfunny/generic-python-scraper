import json
import os
import platform
import re
import time
import pandas as pd
import wget

from selenium import webdriver

from utils.config import WEBDRIVER_DIR
from utils.logging import ScraperLogger


def initialize_chrome_driver(maximized=True, printable=False, save_dir=None):
    options = webdriver.ChromeOptions()
    # options.add_argument('--headless')
    # options.add_argument('--no-sandbox')
    if maximized:
        options.add_argument('--start-maximized')
    else:
        options.add_argument("window-size=800,600")
    desired_capabilities = options.to_capabilities()
    # driver = webdriver.Chrome(executable_path='/usr/lib/chromium-browser/chromedriver', chrome_options=options)
    # driver = webdriver.Chrome(desired_capabilities=desired_capabilities)
    os_type = platform.system()
    if os_type == 'Linux':
        executable_path = f'{WEBDRIVER_DIR}/chromedriver'
    elif os_type == 'Windows':
        executable_path = f'{WEBDRIVER_DIR}/chromedriver.exe'
    else:
        executable_path = ''

    if printable:
        settings = {
            "recentDestinations": [{
                "id": "Save as PDF",
                "origin": "local",
                "account": "",
            }],
            "selectedDestinationId": "Save as PDF",
            "version": 2
        }
        prefs = {'printing.print_preview_sticky_settings.appState': json.dumps(settings)}
        if save_dir:
            prefs['savefile.default_directory'] = save_dir
        options.add_experimental_option('prefs', prefs)
        options.add_argument('--kiosk-printing')

    driver = webdriver.Chrome(executable_path=executable_path, chrome_options=options)

    return driver


def scroll_to_bottom(driver, time_delay=5):
    total_height = 0
    distance = 600

    while True:
        last_height = driver.execute_script("return document.body.scrollHeight")

        driver.execute_script("window.scrollBy({left: 0, top: 600, behavior: 'smooth'});")
        total_height += distance

        time.sleep(time_delay)

        if total_height > last_height:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            break

    return driver.page_source


def write_results_to_json(feed_uri, items, write_mode='w'):
    with open(feed_uri, write_mode, encoding='utf-8') as outfile:
        # outfile.write('[\n')
        item_count = len(items)
        for index, item in enumerate(items):
            json.dump(item, outfile, ensure_ascii=False)
            if index < item_count - 1:
                outfile.write(',')
            outfile.write('\n')
        # outfile.write(']')
        outfile.close()


def write_results_to_txt(feed_uri, item_urls, f_open_mode="w"):
    _f_open_mode = f_open_mode if os.path.exists(feed_uri) else 'w'

    with open(feed_uri, f_open_mode) as f:
        for url in item_urls:
            f.write(f'{url}\n')


def convert_txt_to_json(src_f_path, dst_f_path):
    item_urls = []
    with open(src_f_path, "r") as f:
        items = f.readlines()

        for item in items:
            item = item.replace('\n', '')
            sub_category = item.split(', ')[0]
            item_url = item.split(', ')[1]

            item_urls.append({
                'sub_category': sub_category,
                'item_url': item_url
            })
        f.close()

    write_results_to_json(dst_f_path, item_urls)


def validate_parameter(argv, parameter_count=1):
    logger = ScraperLogger(label='MAIN', log_file='main.log').logger
    if len(argv) < parameter_count:
        logger.info('Parameter is required !!!')
        exit(1)


def write_results_to_csv(output_f_path, items):
    df = pd.DataFrame(items)
    if os.path.exists(output_f_path):
        df.to_csv(output_f_path, mode='a', header=False, index=False)
    else:
        df.to_csv(output_f_path, index=False)


def read_file(f_path, file_format='csv'):
    result = []

    if not os.path.exists(f_path):
        return result

    if file_format == 'csv':
        df = pd.read_csv(f_path)
        result = df.to_dict('records')
    elif file_format == 'txt':
        with open(f_path, "r") as f:
            result = f.read().splitlines()
    else:
        pass

    return result


def download_image_by_wget(url_list, output_dir, failed_file_path):
    failed_urls = []
    for img_url in url_list:
        try:
            image_filename = wget.download(url=img_url, out=output_dir)
            time.sleep(30)
        except Exception as e:
            print('Downloaded Failed: ', img_url)
            failed_urls.append(img_url)
            continue

        print('Successfully Downloaded: ', image_filename)

    if len(failed_urls) > 0:
        with open(failed_file_path, "a") as f:
            for url in failed_urls:
                f.write(f'{url}\n')


def extract_substr_between_two_marks(text, mark1, mark2):
    m = re.search(f'{mark1}(.+?){mark2}', text)
    return m.group(1) if m else None
