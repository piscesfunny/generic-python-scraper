import sys

from custom_scraper.stdaily import STDailySpider
from custom_scraper.sciencedaily import ScienceDailySpider

if __name__ == '__main__':
    spider_name = sys.argv[1]

    if spider_name == "stdaily":
        spider = STDailySpider(
            start_date=sys.argv[2],
            end_date=sys.argv[3],
        )
        skip_item_list = True if sys.argv[4] == "yes" else False
        spider.run(skip_item_list=skip_item_list)
    elif spider_name == "sciencedaily":
        spider = ScienceDailySpider(
            start_date=sys.argv[2],
            end_date=sys.argv[3],
        )
        skip_item_list = True if sys.argv[4] == "yes" else False
        spider.run(skip_item_list=skip_item_list)
