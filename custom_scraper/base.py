import os

from utils.config import OUTPUT_LIST_DIR, OUTPUT_RESULT_DIR, OUTPUT_STATUS_DIR


class CustomBaseSpider(object):
    def __init__(
        self,
        site_name,
        base_url,
    ):
        self.site_name = site_name
        self.base_url = base_url

        self.item_list_dir = os.path.join(OUTPUT_LIST_DIR, site_name)
        self.result_dir = os.path.join(OUTPUT_RESULT_DIR, site_name)
        self.status_dir = os.path.join(OUTPUT_STATUS_DIR, site_name)
        os.makedirs(self.item_list_dir, exist_ok=True)
        os.makedirs(self.result_dir, exist_ok=True)
        os.makedirs(self.status_dir, exist_ok=True)
