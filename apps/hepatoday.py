from scrapy.crawler import CrawlerProcess

from generic_scraper.spiders.hepatoday import HepaTodaySpider
from utils.constants import ACTION_SCRAPPING


def start_scrapper(
    site_name,
    action_type,
    scraping_target,
    start_vol_idx,
    end_vol_idx,
):
    print(f">>> {site_name}")
    if action_type == ACTION_SCRAPPING:
        process = CrawlerProcess()
        process.crawl(HepaTodaySpider, param={
            'scraping_target': scraping_target,
            'start_vol_idx': int(start_vol_idx),
            'end_vol_idx': int(end_vol_idx),
        })

        process.start()
    else:
        pass
