import os.path
import time
from datetime import datetime

from scrapy import Selector
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from custom_scraper.base import CustomBaseSpider
from utils.helpers import initialize_chrome_driver, write_results_to_txt, read_file


class ScienceDailySpider(CustomBaseSpider):
    def __init__(self, start_date, end_date):
        super(ScienceDailySpider, self).__init__(
            site_name="sciencedaily",
            base_url="https://www.sciencedaily.com",
        )
        self.start_date = start_date
        self.end_date = end_date

    def run(self, skip_item_list=False):
        list_f_path = os.path.join(self.item_list_dir, f"list_{self.start_date}_{self.end_date}.txt")

        if skip_item_list:
            items = read_file(list_f_path, file_format="txt")
        else:
            driver = initialize_chrome_driver()
            driver.get(f"{self.base_url}/news")
            WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, 'directory')))
            time.sleep(5)

            # scroll down
            driver.execute_script("window.scrollBy({left: 0, top: 600, behavior: 'smooth'});")
            time.sleep(5)

            # remove element with id `fixed_container_bottom`
            driver.execute_script("""
            var element = document.querySelector("#fixed_container_bottom");
            if (element)
                element.parentNode.removeChild(element);
            """)

            all_iframes = driver.find_elements(By.TAG_NAME, "iframe")
            if len(all_iframes) > 0:
                print("Ad Found\n")
                driver.execute_script("""
                    var elems = document.getElementsByTagName("iframe"); 
                    for(var i = 0, max = elems.length; i < max; i++)
                         {
                             elems[i].hidden=true;
                         }
                                      """)
                print('Total Ads: ' + str(len(all_iframes)))
            else:
                print('No frames found')

            driver.find_element(By.CSS_SELECTOR, 'ul#list > li:last-child > a').click()
            time.sleep(1)

            for i in range(0, 2):
                driver.find_element(By.ID, 'load_more_stories').click()
                time.sleep(1)

            el_selector = Selector(text=driver.page_source)
            weekdays = el_selector.css('div#headlines h3.headlines-date::text').getall()
            n_weekdays = 0
            start_date_dt = datetime.strptime(self.start_date, "%Y-%m-%d")
            for weekday in weekdays:
                dt = datetime.strptime(weekday, "%A, %B %d, %Y")
                if dt < start_date_dt:
                    break
                n_weekdays += 1

            total_news_elems = el_selector.css('#headlines > ul') + el_selector.css('#headlines > div > div > ul')
            news_elems = total_news_elems[:n_weekdays]
            urls = []
            for el in news_elems:
                urls_per_day = el.css('li > a::attr(href)').getall()
                urls += urls_per_day

            full_urls = [self.base_url + url for url in urls]
            items = list(set(full_urls))
            write_results_to_txt(list_f_path, items)

            driver.close()

        success_f_name = os.path.splitext(os.path.basename(list_f_path))[0]
        success_f_path = os.path.join(self.status_dir, f'{success_f_name}_success.txt')
        _prev_success_urls = read_file(success_f_path, 'txt') if os.path.exists(success_f_path) else []
        prev_success_urls = list(set(_prev_success_urls))


        # Start downloading
        driver = initialize_chrome_driver(maximized=False, printable=True, save_dir=self.result_dir)
        current_success_urls = []
        for url in items:
            if url in prev_success_urls:
                print(f"Skipped - request_url: {url}")
                continue

            driver.get(url)
            WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, 'story_text')))
            # Save the PDF
            driver.execute_script("window.print();")  # Chrome-specific command to save page as PDF
            time.sleep(5)

            current_success_urls.append(url)
            write_results_to_txt(success_f_path, [url], "a")

        success_urls = prev_success_urls + current_success_urls
        write_results_to_txt(success_f_path, success_urls, "w")
