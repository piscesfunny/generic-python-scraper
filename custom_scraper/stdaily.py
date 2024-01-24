import os
import time
from datetime import datetime

import pyautogui
import requests

from scrapy import Selector
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from custom_scraper.base import CustomBaseSpider
from utils.cleaner import clean_extra_whitespace
from utils.config import HEADERS, DEFAULT_REQUEST_TIMEOUT, DEFAULT_WEB_DRIVER_WAIT_TIMEOUT
from utils.helpers import write_results_to_csv, read_file, initialize_chrome_driver


class STDailySpider(CustomBaseSpider):
    def __init__(self, start_date, end_date):
        super(STDailySpider, self).__init__(
            site_name="stdaily",
            base_url="http://www.stdaily.com",
        )

        self.start_date = start_date
        self.end_date = end_date

    def run(self, skip_item_list=False):
        list_f_path = os.path.join(self.item_list_dir, f"list_{self.start_date}_{self.end_date}")
        items = []
        urls = []

        if skip_item_list:
            items = read_file(list_f_path)
        else:
            start_urls = [
                f"{self.base_url}/guoji/zongbian/zbjqd.shtml",
                f"{self.base_url}/guoji/shidian/jrsd.shtml",
                f"{self.base_url}/guoji/xinwen/kjxw.shtml",
                f"{self.base_url}/guoji/xinwen/kjxw_2.shtml",
                f"{self.base_url}/guoji/xinwen/kjxw_3.shtml",
            ]

            start_date_dt = datetime.strptime(self.start_date, "%Y-%m-%d")
            end_date_dt = datetime.strptime(self.end_date, "%Y-%m-%d")
            for url in start_urls:
                res = requests.get(url=url, headers=HEADERS, timeout=DEFAULT_REQUEST_TIMEOUT)
                print(f"send request: {url}")
                selector = Selector(text=res.text)
                item_list_selector = selector.css("div.f_lieb_list > dl")
                for item_selector in item_list_selector:
                    _item_date = item_selector.css("div.dete > span::text").get()
                    item_date = clean_extra_whitespace(_item_date)
                    item_date_dt = datetime.strptime(item_date, "%Y-%m-%d %H:%M")
                    if start_date_dt <= item_date_dt <= end_date_dt:
                        item_title = item_selector.css("h3 > a::text").get()
                        _item_url = item_selector.css("h3 > a::attr(href)").get()
                        item_url = f"{self.base_url}{_item_url}"

                        if item_url in urls:
                            continue

                        items.append({
                            "title": item_title,
                            "item_date": item_date,
                            "item_url": item_url,
                        })
                        urls.append(item_url)
                time.sleep(3)
            write_results_to_csv(list_f_path, items)

        driver = initialize_chrome_driver(maximized=False, printable=True, save_dir=self.result_dir)
        for idx, item in enumerate(items):
            url = item.get("item_url")
            driver.get(url)
            WebDriverWait(driver, DEFAULT_WEB_DRIVER_WAIT_TIMEOUT
                          ).until(EC.presence_of_element_located((By.ID, "btnPrint")))
            driver.find_element_by_id("btnPrint").click()
            time.sleep(3)

            pyautogui.hotkey('ctrl', 's')
            time.sleep(3)

            pyautogui.press('enter')
            time.sleep(2)

            print(f"progress: {idx}/{len(items)} files downloaded")

        driver.close()
