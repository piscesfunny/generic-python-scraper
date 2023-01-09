from scrapy.crawler import CrawlerProcess

from generic_scraper.spiders.kjdb import KJDBSpider
from utils.config import *


def start_scrapper(site_name, action_type, target_start_num=None, target_end_num=None, scraping_target=None):
    feed_format = 'csv'

    category_file_path = os.path.join(OUTPUT_DIR, f'{site_name}_categories.{feed_format}')
    result_list_suc_f_path = os.path.join(OUTPUT_LIST_DIR, f'{site_name}_list.{feed_format}')
    result_list_err_f_path = os.path.join(OUTPUT_LIST_DIR, f'{site_name}_list_err.{feed_format}')

    process = CrawlerProcess()

    process.crawl(KJDBSpider, param={
        'action_type': action_type,
        'target_start_num': target_start_num,
        'target_end_num': target_end_num,
        'scraping_target': scraping_target,
        'category_file_path': category_file_path,
        'result_list_suc_f_path': result_list_suc_f_path,
        'result_list_err_f_path': result_list_err_f_path
    })

    process.start()


if __name__ == '__main__':
    start_scrapper()
