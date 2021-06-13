import os
import threading

import wget
from scrapy.crawler import CrawlerProcess
from utils.config import *
from utils.constants import *
from generic_scraper.spiders.alibaba import AlibabaSpider
from utils.logging import ScraperLogger


def start_scrapper(site_name, action_type, target_category=None, scraping_target=None, base_category='farm'):
    logger = ScraperLogger(label='APPS', log_file='alibaba.log').logger
    if action_type == ACTION_GET_CATEGORY:
        feed_format = 'json'
        feed_uri = os.path.join(OUTPUT_DIR, f'{site_name}_categories.{feed_format}')
    elif action_type == ACTION_SCRAPPING:
        if scraping_target == SCRAPPING_TARGET_LIST:
            feed_format = 'json'
            feed_uri = os.path.join(OUTPUT_LIST_DIR, f'{site_name}_{target_category}_list.{feed_format}')
        else:
            feed_format = 'json'
            feed_uri = os.path.join(OUTPUT_RESULT_DIR, f'{site_name}_{target_category}_result.{feed_format}')
    else:
        pass

    logger.info(f'feed_uri: {feed_uri}')

    list_file_path = os.path.join(OUTPUT_LIST_DIR, f'{site_name}_{target_category}_list.{feed_format}')
    media_urls_file_path = os.path.join(OUTPUT_MEDIA_URL_LIST_DIR, f'{site_name}_{target_category}_media_urls.txt')

    if os.path.exists(feed_uri):
        os.remove(feed_uri)

    if os.path.exists(media_urls_file_path):
        os.remove(media_urls_file_path)

    settings = {
        'FEED_FORMAT': feed_format,
        'FEED_URI': feed_uri,
        'FEED_EXPORT_ENCODING': 'utf-8'
    }

    process = CrawlerProcess(settings=settings)

    process.crawl(AlibabaSpider, param={
        'action_type': action_type,
        'target_category': target_category,
        'scraping_target': scraping_target,
        'list_file_path': list_file_path,
        'media_urls_file_path': media_urls_file_path,
        'base_category': base_category,
    })

    process.start()


def start_downloader(site_name, existing_fns, target_category, file_count_per_thread, action_type):
    media_urls_file_path = os.path.join(OUTPUT_MEDIA_URL_LIST_DIR, f'{site_name}_{target_category}_media_urls.txt')
    filtered_file_path = os.path.join(
        OUTPUT_MEDIA_URL_LIST_DIR, f'{site_name}_{target_category}_media_urls_filtered.txt'
    )
    failed_file_path = os.path.join(OUTPUT_MEDIA_URL_LIST_DIR, f'{site_name}_{target_category}_media_urls_failed.txt')

    if os.path.exists(failed_file_path):
        os.remove(failed_file_path)

    filtered_url_list = []
    with open(media_urls_file_path, "r") as f:
        raw_url_list = f.readlines()

        for raw_url in raw_url_list:
            url = raw_url.replace('\n', '')
            if url in filtered_url_list:
                continue

            filtered_url_list.append(url)

        f.close()

    with open(filtered_file_path, "w") as f:
        for url in filtered_url_list:
            f.write(f'{url}\n')

        f.close()

    if action_type == ACTION_DOWNLOAD:
        url_list = []
        for url in filtered_url_list:
            fn = os.path.split(url)[1]
            if fn in existing_fns:
                continue

            url_list.append(url)

        total_count = len(url_list)
        # file_count_per_thread = 400
        file_count_per_thread = int(file_count_per_thread)
        thread_count = total_count // file_count_per_thread + 1

        print(f'Total Count: {total_count}')
        print(f'File Count Per Thread: {file_count_per_thread}')

        threads = []

        for x in range(thread_count):
            start_number_in_thread = x * file_count_per_thread
            end_number_in_thread = start_number_in_thread + file_count_per_thread
            if x == thread_count - 1:
                url_list_per_thread = url_list[start_number_in_thread:]
            else:
                url_list_per_thread = url_list[start_number_in_thread:end_number_in_thread]
            get_partial_images_thread = threading.Thread(target=download_image_by_wget, args=[
                url_list_per_thread, failed_file_path
            ])

            get_partial_images_thread.start()
            threads.append(get_partial_images_thread)

        for thread in threads:
            thread.join()

        print('Download Finished !!!')


def download_image_by_wget(url_list, failed_file_path):
    failed_urls = []
    for img_url in url_list:
        try:
            image_filename = wget.download(url=img_url, out=OUTPUT_MEDIA_DIR)
        except:
            print('Downloaded Failed: ', img_url)
            failed_urls.append(img_url)
            continue

        print('Successfully Downloaded: ', image_filename)

    with open(failed_file_path, "a") as f:
        for url in failed_urls:
            f.write(f'{url}\n')


if __name__ == '__main__':
    start_scrapper()
