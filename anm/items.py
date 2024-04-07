# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class AnmItem(scrapy.Item):
    id = scrapy.Field()
    name = scrapy.Field()
    year = scrapy.Field()
    sinopse = scrapy.Field()
    categories = scrapy.Field()
    rate = scrapy.Field()
    url = scrapy.Field()


class EpItem(scrapy.Item):
    id = scrapy.Field()
    anime_id = scrapy.Field()
    number = scrapy.Field()
    date = scrapy.Field()
    season = scrapy.Field()
    url = scrapy.Field()
