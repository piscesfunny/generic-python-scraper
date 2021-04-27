import sys

from apps.alibaba import start_downloader as alibaba_start_downloader
from apps.alibaba import start_scrapper as alibaba_start_scrapper
from apps.machinio import start_scrapper as machinio_start_scrapper
from apps.machinio import start_downloader as machinio_start_downloader
from apps.japan_agritrading import start_scrapper as japan_agritrading_start_scrapper
from apps.ironplanet import start_scrapper as ironplanet_start_scrapper
from apps.ironplanet import start_downloader as ironplanet_start_downloader
from apps.machinerypete import start_scrapper as machinerypete_start_scrapper
from apps.machinerypete import filter_list as machinerypete_filter_list
from apps.meganorm import start_scrapper as meganorm_start_scrapper
from utils.config import *
from utils.constants import *
from utils.logging import ScraperLogger

if __name__ == '__main__':
    os.makedirs(LOG_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(OUTPUT_LIST_DIR, exist_ok=True)
    os.makedirs(OUTPUT_RESULT_DIR, exist_ok=True)
    os.makedirs(OUTPUT_MEDIA_URL_LIST_DIR, exist_ok=True)
    os.makedirs(OUTPUT_FAILED_DIR, exist_ok=True)

    os.makedirs(OUTPUT_MEDIA_DIR, exist_ok=True)

    existing_fns = [fn for fn in os.listdir(OUTPUT_MEDIA_DIR)]

    logger = ScraperLogger(label='MAIN', log_file='main.log').logger
    if len(sys.argv) < 2:
        logger.info('Parameter required !!!')
    elif len(sys.argv) < 3:
        logger.info('Action type required !!!')
    else:
        if sys.argv[1] == 'alibaba':
            if sys.argv[2] == ACTION_GET_CATEGORY:
                alibaba_start_scrapper(site_name=sys.argv[1], action_type=sys.argv[2], base_category=sys.argv[5])
            elif sys.argv[2] == ACTION_SCRAPPING:
                if len(sys.argv) < 5:
                    logger.info('Target Category or Scraping Target  required !!!')
                else:
                    logger.info(f'{sys.argv[1]}.com spider started')
                    alibaba_start_scrapper(
                        site_name=sys.argv[1],
                        action_type=sys.argv[2],
                        target_category=sys.argv[3],
                        scraping_target=sys.argv[4],
                        base_category=sys.argv[5]
                    )
            elif sys.argv[2] == ACTION_DOWNLOAD:
                alibaba_start_downloader(
                    site_name=sys.argv[1],
                    existing_fns=existing_fns, target_category=sys.argv[3],
                    file_count_per_thread=sys.argv[4], action_type=ACTION_DOWNLOAD
                )
            elif sys.argv[2] == ACTION_FILTER:
                alibaba_start_downloader(
                    site_name=sys.argv[1],
                    existing_fns=existing_fns, target_category=sys.argv[3], file_count_per_thread=sys.argv[4],
                    action_type=ACTION_FILTER
                )
        if sys.argv[1] == 'machinio':
            if sys.argv[2] == ACTION_GET_CATEGORY:
                machinio_start_scrapper(site_name=sys.argv[1], action_type=sys.argv[2])
            elif sys.argv[2] == ACTION_SCRAPPING:
                logger.info(f'{sys.argv[1]}.com spider started')
                machinio_start_scrapper(
                    site_name=sys.argv[1],
                    action_type=sys.argv[2],
                    target_category=sys.argv[3],
                    scraping_target=sys.argv[4]
                )
            elif sys.argv[2] == ACTION_FILTER:
                machinio_start_downloader(
                    site_name=sys.argv[1],
                    existing_fns=existing_fns,
                    target_category=sys.argv[3],
                    file_count_per_thread=sys.argv[4],
                    action_type=ACTION_FILTER
                )
        if sys.argv[1] == 'japan_agritrading':
            if sys.argv[2] == ACTION_GET_CATEGORY:
                japan_agritrading_start_scrapper(site_name=sys.argv[1], action_type=sys.argv[2])
            elif sys.argv[2] == ACTION_SCRAPPING:
                logger.info(f'{sys.argv[1]}.com spider started')
                japan_agritrading_start_scrapper(
                    site_name=sys.argv[1],
                    action_type=sys.argv[2],
                    target_category=sys.argv[3],
                    scraping_target=sys.argv[4]
                )
        if sys.argv[1] == 'ironplanet':
            if sys.argv[2] == ACTION_GET_CATEGORY:
                ironplanet_start_scrapper(site_name=sys.argv[1], action_type=sys.argv[2])
            elif sys.argv[2] == ACTION_SCRAPPING:
                logger.info(f'{sys.argv[1]}.com spider started')
                ironplanet_start_scrapper(
                    site_name=sys.argv[1],
                    action_type=sys.argv[2],
                    target_category=sys.argv[3],
                    scraping_target=sys.argv[4]
                )
            elif sys.argv[2] == ACTION_FILTER:
                ironplanet_start_downloader(
                    site_name=sys.argv[1],
                    existing_fns=existing_fns,
                    target_category=sys.argv[3],
                    file_count_per_thread=sys.argv[4],
                    action_type=ACTION_FILTER
                )
        if sys.argv[1] == 'machinerypete':
            if sys.argv[2] == ACTION_GET_CATEGORY:
                machinerypete_start_scrapper(site_name=sys.argv[1], action_type=sys.argv[2])
            elif sys.argv[2] == ACTION_SCRAPPING:
                logger.info(f'{sys.argv[1]}.com spider started')
                machinerypete_start_scrapper(
                    site_name=sys.argv[1],
                    action_type=sys.argv[2],
                    target_category=sys.argv[3],
                    scraping_target=sys.argv[4]
                )
            elif sys.argv[2] == ACTION_FILTER:
                machinerypete_filter_list(
                    site_name=sys.argv[1],
                    target_category=sys.argv[3]
                )
        if sys.argv[1] == 'meganorm':
            if sys.argv[2] == ACTION_GET_CATEGORY:
                meganorm_start_scrapper(site_name=sys.argv[1], action_type=sys.argv[2])
            elif sys.argv[2] == ACTION_SCRAPPING:
                logger.info(f'{sys.argv[1]}.com spider started')
                meganorm_start_scrapper(
                    site_name=sys.argv[1],
                    action_type=sys.argv[2],
                    target_category=sys.argv[3],
                    scraping_target=sys.argv[4]
                )
