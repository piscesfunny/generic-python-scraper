import os

from dotenv import load_dotenv

UTILS_DIR = os.path.dirname(os.path.realpath(__file__))
BASE_DIR = os.path.realpath(os.path.join(UTILS_DIR, os.pardir))

load_dotenv(os.path.join(BASE_DIR, '.env'))

SCRAPER_API_KEY = os.getenv('SCRAPER_API_KEY')

OUTPUT_DIR = os.path.join(BASE_DIR, 'output')
OUTPUT_LIST_DIR = os.path.join(OUTPUT_DIR, 'list')
OUTPUT_RESULT_DIR = os.path.join(OUTPUT_DIR, 'result')
OUTPUT_MEDIA_URL_LIST_DIR = os.path.join(OUTPUT_DIR, 'media_url_list')

OUTPUT_MEDIA_DIR = os.path.join(OUTPUT_DIR, 'media')
OUTPUT_IMG_DIR = os.path.join(OUTPUT_DIR, 'img')
OUTPUT_VIDEO_DIR = os.path.join(OUTPUT_DIR, 'video')
OUTPUT_DOC_DIR = os.path.join(OUTPUT_DIR, 'doc')

LOG_DIR = os.path.join(BASE_DIR, 'logs')
WEBDRIVER_DIR = os.path.join(BASE_DIR, 'webdriver')

PAGE_COUNT_PER_THREAD = os.getenv('PAGE_COUNT_PER_THREAD')
