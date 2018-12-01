# -*- coding: utf-8 -*-
import scrapy


class BossSpider(scrapy.Spider):
    name = 'Boss'
    allowed_domains = ['zhipin.com']
    start_urls = ['http://zhipin.com/']

    def parse(self, response):
        pass
