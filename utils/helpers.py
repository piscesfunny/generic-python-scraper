import json
import time

from selenium import webdriver

from utils.config import WEBDRIVER_DIR


def initialize_chrome_driver():
    options = webdriver.ChromeOptions()
    # options.add_argument('--headless')
    # options.add_argument('--no-sandbox')
    options.add_argument('--start-maximized')
    desired_capabilities = options.to_capabilities()
    # driver = webdriver.Chrome(executable_path='/usr/lib/chromium-browser/chromedriver', chrome_options=options)
    # driver = webdriver.Chrome(desired_capabilities=desired_capabilities)

    driver = webdriver.Chrome(executable_path=f'{WEBDRIVER_DIR}/chromedriver', chrome_options=options)

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


def write_results_to_json(feed_uri, item_urls):
    with open(feed_uri, 'w', encoding='utf-8') as outfile:
        outfile.write('[\n')
        item_count = len(item_urls)
        for index, item in enumerate(item_urls):
            json.dump(item, outfile, ensure_ascii=False)
            if index < item_count - 1:
                outfile.write(',')
            outfile.write('\n')
        outfile.write(']')
        outfile.close()
