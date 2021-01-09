import scrapy

from scrapy.item import Item, Field
from scrapy.loader.processors import MapCompose, Join


class FarmMachineryItem(Item):
    name = Field(
        input_processor=MapCompose(str.strip),
        output_processor=Join()
    )
    category = Field(
        input_processor=MapCompose(str.strip),
        output_processor=Join()
    )
    quick_details = Field(
        input_processor=MapCompose(str.strip),
        output_processor=Join()
    )
    description = Field(
        input_processor=MapCompose(str.strip),
        output_processor=Join()
    )
    specification = Field(
        input_processor=MapCompose(str.strip),
        output_processor=Join()
    )
    img_urls = Field(
        input_processor=MapCompose(str.strip),
        output_processor=Join()
    )
    video_urls = Field(
        input_processor=MapCompose(str.strip),
        output_processor=Join()
    )
    doc_urls = Field(
        input_processor=MapCompose(str.strip),
        output_processor=Join()
    )
