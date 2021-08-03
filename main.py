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
from apps.meganorm import get_failed_list_json as meganorm_get_failed_list_json
from apps.steelnumber import start_scrapper as steelnumber_start_scrapper
from apps.steeljis import start_scrapper as steeljis_start_scrapper
from apps.refractories_worldforum import start_scrapper as refractories_worldforum_start_scrapper
from apps.hindawi import start_scrapper as hindawi_start_scrapper
from apps.sweets_construction import start_scrapper as sweets_construction_start_scrapper
from utils.config import *
from utils.constants import *
from utils.helpers import validate_parameter
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

    sites_with_three_parameter = [
        'alibaba', 'machinio', 'japan_agritrading', 'ironplanet', 'machinerypete', 'meganorm', 'steelnumber',
        'steeljis', 'refractories_worldforum'
    ]

    if sys.argv[1] in sites_with_three_parameter:
        validate_parameter(sys.argv, parameter_count=3)

    if sys.argv[1] == 'alibaba':
        base_category = sys.argv[5] if len(sys.argv) > 5 else 'farm'
        specific_category_url = sys.argv[6] if len(sys.argv) > 6 else ''
        total_page_count = sys.argv[7] if len(sys.argv) > 7 else 1
        start_page_number = sys.argv[8] if len(sys.argv) > 8 else 1
        if sys.argv[2] == ACTION_GET_CATEGORY:
            alibaba_start_scrapper(site_name=sys.argv[1], action_type=sys.argv[2], base_category=base_category)
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
                    base_category=base_category,
                    specific_category_url=specific_category_url,
                    total_page_count=total_page_count,
                    start_page_number=start_page_number
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
            meganorm_start_scrapper(site_name=sys.argv[1], action_type=sys.argv[2], target_category=sys.argv[3])
        elif sys.argv[2] == ACTION_SCRAPPING:
            logger.info(f'{sys.argv[1]}.com spider started')
            meganorm_start_scrapper(
                site_name=sys.argv[1],
                action_type=sys.argv[2],
                target_category=sys.argv[3],
                scraping_target=sys.argv[4]
            )
        elif sys.argv[2] == ACTION_CONVERT:
            meganorm_get_failed_list_json(site_name=sys.argv[1], target_category=sys.argv[3])
    if sys.argv[1] == 'steelnumber':
        steelnumber_start_scrapper(site_name=sys.argv[1], target_category=sys.argv[2])
    if sys.argv[1] == 'steeljis':
        steeljis_start_scrapper(site_name=sys.argv[1], target_category=sys.argv[2])
    if sys.argv[1] == 'refractories_worldforum':
        refractories_worldforum_start_scrapper(
            site_name=sys.argv[1], target_category=sys.argv[2], page_count=sys.argv[3]
        )
    if sys.argv[1] == 'hindawi':
        hindawi_start_scrapper(site_name=sys.argv[1])

    if sys.argv[1] == 'sweets_construction':
        sweets_construction_start_scrapper(site_name=sys.argv[1], scraping_target=sys.argv[2])
