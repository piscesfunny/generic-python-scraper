import os
import string
import time

from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By

from custom_scraper.base import CustomBaseSpider
from utils.cleaner import clean_extra_whitespace, clean_characters_for_folder_name
from utils.helpers import read_file, initialize_chrome_driver, scroll_to_bottom, write_results_to_csv, download_file


class WorldOfConcreteSpider(CustomBaseSpider):
    def __init__(self):
        super(WorldOfConcreteSpider, self).__init__(
            site_name="worldofconcrete",
            base_url="https://www.worldofconcrete.com/",
        )

    def run(self, skip_item_list=False):
        list_f_path = os.path.join(self.item_list_dir, f"list_exhibitors.csv")
        sub_base_url = "https://ge24woc.mapyourshow.com"

        if skip_item_list:
            items = read_file(list_f_path)
        else:
            driver = initialize_chrome_driver()
            alphabet = string.ascii_uppercase
            items = []
            for idx, c in enumerate(alphabet):
                url = f"{sub_base_url}/8_0/explore/exhibitor-alphalist.cfm?nav=1#/alpha/{c}"
                driver.get(url)
                print(f"fetching urls - {idx+1}/{len(alphabet)} - {url}")
                scroll_to_bottom(driver, time_delay=1)
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                item_elements = soup.select("#exhibitor-results tr")
                sub_items = []
                for el in item_elements:
                    try:
                        link_el = el.select_one("td.is-hidden_small > span > div > a")
                        if not link_el:
                            continue
                        item_url = f"{sub_base_url}{link_el.attrs.get('href')}"
                        item_title = el.select_one("h3.card-Title > a > span").text
                        item_title = clean_extra_whitespace(item_title).replace(",", "_").replace("_ ", "_")
                        item_title = clean_characters_for_folder_name(item_title)
                        sub_items.append({
                            "item_title": item_title,
                            "item_url": item_url,
                        })
                    except Exception as e:
                        print(f"Failed! - url: {url}")
                        print(e)
                items += sub_items

            write_results_to_csv(list_f_path, items)
            driver.close()

        # Start downloading
        success_f_path = os.path.join(self.status_dir, "exhibitors_success.csv")
        success_items = read_file(success_f_path)
        success_item_urls = [item.get("item_url") for item in success_items]
        success_item_urls = list(set(success_item_urls))
        for idx, item in enumerate(items):
            progress = f"{idx + 1}/{len(items)}"
            item_url = item.get("item_url")
            exhibitor = item.get("item_title", f"unknown_{idx}")
            if item_url in success_item_urls:
                print(f"Already downloaded - {progress} - url: {item_url} - exhibitor: {exhibitor}")
                continue

            save_dir = os.path.join(self.result_dir, str(exhibitor))
            driver = initialize_chrome_driver(printable=True, save_dir=save_dir)
            try:
                print(f"downloading - {progress} - url: {item_url} - exhibitor: {exhibitor}")
                driver.get(item_url)
                time.sleep(2)
                driver.execute_script("window.scrollBy({left: 0, top: 600, behavior: 'smooth'});")

                thumbnail_elements = driver.find_elements(By.CSS_SELECTOR, "div.showcase-thumbnails > figure > a")
                media_items = []
                for i, e in enumerate(thumbnail_elements):
                    e.click()
                    time.sleep(2)
                    soup = BeautifulSoup(driver.page_source, 'html.parser')
                    video_el = soup.select_one("div.showroom-media-image_wrapper video")
                    video_url = video_el.attrs.get("src") if video_el else None
                    image_el = soup.select_one("div.showroom-media-image_wrapper img")
                    image_url = image_el.attrs.get("src") if image_el else None
                    if video_url:
                        media_items.append({"media_type": "video", "url": video_url})
                    if image_url:
                        media_items.append({"media_type": "image", "url": image_url})

                if not media_items:
                    print("No content")
                    success_items = [{"item_title": exhibitor, "item_url": item_url}]
                    write_results_to_csv(success_f_path, success_items)
                    driver.close()
                    continue

                os.makedirs(save_dir, exist_ok=True)
                for item in media_items:
                    media_url = item.get("url")
                    media_type = item.get("media_type")
                    if media_type == "image":
                        f_name = f"{os.path.basename(media_url)[-64:]}.png"
                    else:
                        f_name = os.path.basename(media_url)
                    f_path = os.path.join(save_dir, f_name)
                    download_file(media_url, f_path)

                scroll_to_bottom(driver, time_delay=1)
                driver.execute_script("window.print();")

                success_items = [{"item_title": exhibitor, "item_url": item_url}]
                write_results_to_csv(success_f_path, success_items)
            except Exception as e:
                print(e)

            driver.close()
