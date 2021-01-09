import os

from dotenv import load_dotenv

UTILS_DIR = os.path.dirname(os.path.realpath(__file__))
BASE_DIR = os.path.realpath(os.path.join(UTILS_DIR, os.pardir))

load_dotenv(os.path.join(BASE_DIR, '.env'))

SCRAPER_API_KEY = os.getenv('SCRAPER_API_KEY')

OUTPUT_DIR = os.path.join(BASE_DIR, 'output')

LOG_DIR = os.path.join(BASE_DIR, 'logs')

PAGE_COUNT_PER_THREAD = os.getenv('PAGE_COUNT_PER_THREAD')
