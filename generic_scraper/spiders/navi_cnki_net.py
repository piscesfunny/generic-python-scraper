import time
from pathlib import Path

import requests
import scrapy
from scrapy.selector import Selector
from scrapy.utils.project import get_project_settings
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from config.config import Config
from utils.config import *
from utils.constants import *
from utils.helpers import initialize_chrome_driver, write_results_to_csv, read_file, \
    write_results_to_txt, download_image_by_wget
from utils.logging import ScraperLogger


class NaviCNKISpider(scrapy.Spider):
    name = 'navi_cnki_net'
    allowed_domains = ['www.baidu.com', 'baidu.com']
    start_urls = ['https://www.baidu.com/']

    base_url = 'https://navi.cnki.net/knavi'

    logger = None

    def __init__(self, param):
        super(NaviCNKISpider, self).__init__()

        self.logger = ScraperLogger(label='SPIDER', log_file=f'{self.name}.log').logger

        self.default_headers = {
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko)'
                          ' Chrome/74.0.3729.131 Safari/537.36'
        }

        self.action_type = param['action_type']
        self.scraping_target = param['scraping_target']
        self.target_category = param['target_category']
        self.category_file_path = param['category_file_path']
        self.result_list_suc_f_path = param['result_list_suc_f_path']
        self.result_list_err_f_path = param['result_list_err_f_path']

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url=url, callback=self.parse, headers=self.default_headers)

    def parse(self, response):
        headers = self.default_headers
        headers['referer'] = response.request.url
        delay = 5

        category_urls = [
            'https://navi.cnki.net/knavi/journals/GJTK/detail'
        ]
        driver = initialize_chrome_driver()
        driver = self.login(driver)

        category_url = category_urls[0]
        driver.get(category_url)
        year = int(self.target_category) if self.target_category else 0
        if year < 2003:
            WebDriverWait(driver, 30).until(EC.presence_of_element_located((
                By.XPATH, "//*[@id='leftYearTree']/div/div[2]/a[2]")))
            driver.find_element(By.XPATH, "//*[@id='leftYearTree']/div/div[2]/a[2]").click()
            time.sleep(2)

        year_elem_id = f"{self.target_category}_Year_Issue"
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((
            By.ID, year_elem_id)))
        time.sleep(2)
        driver.find_element(By.ID, year_elem_id).click()
        time.sleep(2)

        issue_elems = driver.find_element(By.ID, year_elem_id).find_elements(By.CSS_SELECTOR, "a")
        items = []
        issue_elems.reverse()
        start_issue = int(self.scraping_target) if self.scraping_target else 1
        for i, issue_elem in enumerate(issue_elems):
            if i < start_issue - 1:
                continue
            issue_elem.click()
            WebDriverWait(driver, 30).until(EC.presence_of_element_located((
                By.CSS_SELECTOR, "#CataLogContent ul li:first-child a")))
            time.sleep(2)
            issue = issue_elem.text
            # scrapy_selector = Selector(text=driver.page_source)
            # article_elems = scrapy_selector.css("#CataLogContent ul li:first-child")
            article_elems = driver.find_elements(By.CSS_SELECTOR, "#CataLogContent .row.clearfix")
            for article_elem in article_elems:
                # hover = ActionChains(driver).move_to_element(article_elem)
                # hover.perform()
                # tile = article_elem.text
                link_elem = article_elem.find_elements(By.CSS_SELECTOR, "span.name > a")[0]

                link_elem.click()
                time.sleep(1)

                driver.switch_to.window(driver.window_handles[1])
                driver.find_element(By.ID, "cajDown").click()
                time.sleep(1)

                driver.switch_to.window(driver.window_handles[2])
                driver.find_element(By.ID, "downSubmit").click()
                time.sleep(1)

                driver.close()
                driver.switch_to.window(driver.window_handles[1])

                driver.close()
                driver.switch_to.window(driver.window_handles[0])

                time.sleep(1)

                # article_url = article_elem.css('a::attr(href)').get()
                # item = {
                #     'year': self.target_category,
                #     'issue': issue,
                #     'article_url': article_url
                # }
                # items.append(item)

            downloads_path = str(Path.home() / "Downloads")
            divider_f_name = f"{downloads_path}/{issue}.txt"
            file = open(divider_f_name, 'w+')

        # write_results_to_csv(self.result_list_suc_f_path, items)

    def login(self, driver):
        driver.get("https://www.cnki.net")
        WebDriverWait(driver, 30).until(EC.presence_of_element_located(
                (By.ID, "Ecp_top_login")))
        time.sleep(2)
        driver.find_element(By.ID, "Ecp_top_login").click()

        username = driver.find_element(By.ID, "Ecp_TextBoxUserName")
        password = driver.find_element(By.ID, "Ecp_TextBoxPwd")

        username.send_keys(Config.email)
        password.send_keys(Config.password)

        time.sleep(2)
        driver.find_element(By.ID, "Ecp_Button1").click()

        time.sleep(5)

        return driver
