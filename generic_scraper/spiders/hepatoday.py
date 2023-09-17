import os.path
import re

import scrapy

from utils.config import OUTPUT_LIST_DIR
from utils.helpers import write_results_to_txt
from utils.logging import ScraperLogger


class HepaTodaySpider(scrapy.Spider):
    name = 'hepatoday'
    allowed_domains = ['www.hepatoday.org']
    start_urls = ['http://www.hepatoday.org']

    base_url = 'http://www.hepatoday.org'

    logger = None

    def __init__(self, param):
        super(HepaTodaySpider, self).__init__()

        self.logger = ScraperLogger(label='SPIDER', log_file=f'{self.name}.log').logger

        self.default_headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/114.0.0.0 Safari/537.36'
        }

        self.scraping_target = param['scraping_target']
        self.start_vol_idx = param['start_vol_idx']
        self.end_vol_idx = param['end_vol_idx']

    def start_requests(self):
        for vol in range(self.start_vol_idx, self.end_vol_idx+1):
            url = f"{self.base_url}/CN/volumn/volumn_{vol}.shtml"
            yield scrapy.Request(
                url=url,
                callback=self.parse,
                headers=self.default_headers,
                meta={"vol": vol},
            )

    def parse(self, response, **kwargs):
        print(response)
        vol = response.meta.get("vol")
        if not vol:
            print("Invalid volumn idx")
            return

        title_text = response.css(".dqtab > .njq::text").get()[:15]
        year, vol, no = re.findall(r'\d+', title_text)
        output_f_path = os.path.join(
            OUTPUT_LIST_DIR,
            f"{self.name}-{year}-{vol}-{no}.txt",
        )
        item_selectors = response.css("div.noselectrow")
        pdf_urls = []
        for item_selector in item_selectors:
            pdf_id_text = item_selector.css(".zhaiyao > a")[1].css("::attr(onclick)").get()
            match = re.search(r"'(\d+)'", pdf_id_text)
            pdf_id = match.group(1)
            pdf_url = f"{self.base_url}/CN/article/downloadArticleFile.do?" \
                      f"attachType=PDF&id={pdf_id}"
            pdf_urls.append(pdf_url)

        write_results_to_txt(output_f_path, pdf_urls)
