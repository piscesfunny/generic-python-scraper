from scrapy.crawler import CrawlerProcess

from generic_scraper.spiders.online_epocrates import OnlineEpocratesSpider
from utils.config import *


def start_scrapper(site_name, action_type, target_category=None, scraping_target=None):
    feed_format = 'csv'

    category_file_path = os.path.join(OUTPUT_DIR, f'{site_name}_categories.{feed_format}')
    result_list_suc_f_path = os.path.join(OUTPUT_LIST_DIR, f'{site_name}_list_{target_category}.{feed_format}')
    result_list_err_f_path = os.path.join(OUTPUT_LIST_DIR, f'{site_name}_list_{target_category}_err.{feed_format}')

    process = CrawlerProcess()

    process.crawl(OnlineEpocratesSpider, param={
        'action_type': action_type,
        'scraping_target': scraping_target,
        'target_category': target_category,
        'category_file_path': category_file_path,
        'result_list_suc_f_path': result_list_suc_f_path,
        'result_list_err_f_path': result_list_err_f_path
    })

    process.start()


if __name__ == '__main__':
    start_scrapper()
