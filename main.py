import os
import sys

from utils.config import LOG_DIR
from utils.logging import ScraperLogger

from apps.alibaba import start_scrapper as alibaba_start_scrapper

if __name__ == '__main__':
    os.makedirs(LOG_DIR, exist_ok=True)
    logger = ScraperLogger(label='MAIN', log_file='main.log').logger
    if len(sys.argv) < 2:
        logger.info('Parameter required !!!')
    else:
        if sys.argv[1] == 'alibaba':
            logger.info(f'{sys.argv[1]}.com spider started')
            alibaba_start_scrapper()
