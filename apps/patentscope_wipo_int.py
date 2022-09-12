import pandas as pd

from scrapy.crawler import CrawlerProcess

from generic_scraper.spiders.patentscope_wipo_int import PatentScopeWipoSpider
from utils.config import *
from utils.constants import ACTION_SCRAPPING, ACTION_CONVERT


def start_scrapper(site_name, action_type, target_year=None, target_start_week=None, target_end_week=None,
                   scraping_target=None):
    if action_type == ACTION_SCRAPPING:
        feed_format = 'csv'

        category_file_path = os.path.join(OUTPUT_DIR, f'{site_name}_categories.{feed_format}')
        result_list_suc_f_path = os.path.join(OUTPUT_LIST_DIR, f'{site_name}_list_{target_year}.{feed_format}')
        result_list_err_f_path = os.path.join(OUTPUT_LIST_DIR, f'{site_name}_list_{target_year}_err.{feed_format}')

        feed_uri = os.path.join(
            OUTPUT_RESULT_DIR, f'{site_name}_{target_year}_{target_start_week}_{target_end_week}_result.{feed_format}'
        )

        process = CrawlerProcess()

        process.crawl(PatentScopeWipoSpider, param={
            'action_type': action_type,
            'target_year': target_year,
            'target_start_week': target_start_week,
            'target_end_week': target_end_week,
            'scraping_target': scraping_target,
            'category_file_path': category_file_path,
            'result_list_suc_f_path': result_list_suc_f_path,
            'result_list_err_f_path': result_list_err_f_path,
            'feed_uri': feed_uri
        })

        process.start()

    elif action_type == ACTION_CONVERT:
        for f in os.listdir(OUTPUT_TEMP_DIR):
            input_f_path = os.path.join(OUTPUT_TEMP_DIR, f)
            df = pd.read_excel(input_f_path)
            week_num_list = df.iloc[0, 0].replace('Gazette: ', '').split('/')
            week_num_list.reverse()
            week_num = ''.join(week_num_list)
            df = df.drop(df.index[0])
            output_f_path = os.path.join(OUTPUT_LIST_DIR, f'{site_name}_list_{week_num}.csv')
            df.to_csv(output_f_path, index=None, header=False)
    else:
        pass


if __name__ == '__main__':
    start_scrapper()
