import json
import time
import chromedriver_binary

from selenium import webdriver

# from utils.config import WEBDRIVER_DIR
from utils.logging import ScraperLogger


def initialize_chrome_driver():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    # options.add_argument('--no-sandbox')
    options.add_argument('--start-maximized')
    desired_capabilities = options.to_capabilities()
    # driver = webdriver.Chrome(executable_path='/usr/lib/chromium-browser/chromedriver', chrome_options=options)
    # driver = webdriver.Chrome(desired_capabilities=desired_capabilities)

    driver = webdriver.Chrome(chrome_options=options)

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


def write_results_to_txt(feed_uri, item_urls):
    with open(feed_uri, "w") as f:
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
