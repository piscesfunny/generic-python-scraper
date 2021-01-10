import os
import sys

from utils.config import *
from utils.logging import ScraperLogger
from utils.constants import *

from apps.alibaba import start_scrapper as alibaba_start_scrapper

if __name__ == '__main__':
    os.makedirs(LOG_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(OUTPUT_IMG_DIR, exist_ok=True)
    os.makedirs(OUTPUT_VIDEO_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DOC_DIR, exist_ok=True)

    existing_img_fns = [fn for fn in os.listdir(OUTPUT_IMG_DIR)]
    existing_video_fns = [fn for fn in os.listdir(OUTPUT_VIDEO_DIR)]
    existing_doc_fns = [fn for fn in os.listdir(OUTPUT_DOC_DIR)]

    existing_fns = {
        'existing_img_fns': existing_img_fns,
        'existing_video_fns': existing_video_fns,
        'existing_doc_fns': existing_doc_fns,
    }

    logger = ScraperLogger(label='MAIN', log_file='main.log').logger
    if len(sys.argv) < 2:
        logger.info('Parameter required !!!')
    elif len(sys.argv) < 3:
        logger.info('Action type required !!!')
    else:
        if sys.argv[1] == 'alibaba':
            if sys.argv[2] == ACTION_GET_CATEGORY:
                alibaba_start_scrapper(existing_fns=existing_fns, action_type=sys.argv[2])
            elif sys.argv[2] == ACTION_SCRAPPING:
                if len(sys.argv) < 4:
                    logger.info('Category required !!!')
                else:
                    logger.info(f'{sys.argv[1]}.com spider started')
                    alibaba_start_scrapper(existing_fns, action_type=sys.argv[2], target_category=sys.argv[3])

