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
    sub_category = Field(
        input_processor=MapCompose(str.strip),
        output_processor=Join()
    )
    country = Field(
        input_processor=MapCompose(str.strip),
        output_processor=Join()
    )
    price = Field(
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
    item_url = Field(
        input_processor=MapCompose(str.strip),
        output_processor=Join()
    )
    website = Field(
        input_processor=MapCompose(str.strip),
        output_processor=Join()
    )

    def __repr__(self):
        """only print out attr1 after exiting the Pipeline"""
        return repr({"name": self['name'], "category": self['category']})


class SteelNumberItem(Item):
    category = Field(input_processor=MapCompose(str.strip), output_processor=Join())
    sub_category = Field(input_processor=MapCompose(str.strip), output_processor=Join())
    grade = Field(input_processor=MapCompose(str.strip), output_processor=Join())
    number = Field(input_processor=MapCompose(str.strip), output_processor=Join())
    standards = Field(input_processor=MapCompose(str.strip), output_processor=Join())
    description = Field(input_processor=MapCompose(str.strip), output_processor=Join())
    item_url = Field(input_processor=MapCompose(str.strip), output_processor=Join())
    website = Field(input_processor=MapCompose(str.strip), output_processor=Join())

    def __repr__(self):
        """only print out attr1 after exiting the Pipeline"""
        return repr({"grade": self['grade'], "category": self['category']})


class RefractoryWorldFormItem(Item):
    department = Field(input_processor=MapCompose(str.strip), output_processor=Join())
    title = Field(input_processor=MapCompose(str.strip), output_processor=Join())
    quick_description = Field(input_processor=MapCompose(str.strip), output_processor=Join())
    description = Field(input_processor=MapCompose(str.strip), output_processor=Join())
    doc_path = Field(input_processor=MapCompose(str.strip), output_processor=Join())
    item_url = Field(input_processor=MapCompose(str.strip), output_processor=Join())
    website = Field(input_processor=MapCompose(str.strip), output_processor=Join())

    def __repr__(self):
        """only print out attr1 after exiting the Pipeline"""
        return repr({"department": self['department'], "title": self['title']})
