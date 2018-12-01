# -*- coding: utf-8 -*-
import scrapy
from jobCrawler.items import JobcrawlerItem
from scrapy.http import Request
from scrapy.spiders import CrawlSpider
from scrapy.selector import Selector
import  json
import  time
import  random
import redis
from scrapy.conf import settings
from pyquery import PyQuery as pq

class BossSpider(scrapy.Spider):
    name = 'Boss'
    allowed_domains = ['zhipin.com']
    start_urls = ['https://www.zhipin.com/c101010100/?query=php&page=1']

    current_page = 1 #开始页码
    max_page = 10 #最大页码

    custom_settings = {
        "ITEM_PIPELINES":{
            'jobCrawler.pipelines.ZhipinPipeline': 300,
        },
        "DOWNLOADER_MIDDLEWARES":{
            'jobCrawler.middlewares.ZhipinMiddleware': 299,
         #   'tutorial.middlewares.ProxyMiddleware':301
        },
        "DEFAULT_REQUEST_HEADERS":{
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'User-Agent':'Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/65.0.3325.181 Chrome/65.0.3325.181 Safari/537.36',
            'Referer':'https://www.zhipin.com/c101010100/?query=php',
            "cookie":"lastCity=101010100; Hm_lvt_194df3105ad7148dcf2b98a91b5e727a=1542117498,1542206405,1542637246; __c=1542637246; __g=-; __l=l=%2Fwww.zhipin.com%2Fjob_detail%2F%3Fquery%3Dphp%26scity%3D101010100%26industry%3D%26position%3D&r=; toUrl=https%3A%2F%2Fwww.zhipin.com%2Fjob_detail%2F%3Fquery%3Dphp%26scity%3D101010100%26industry%3D%26position%3D; __a=89906886.1542117495.1542206405.1542637246.19.4.12.19; Hm_lpvt_194df3105ad7148dcf2b98a91b5e727a=1542639989"
        }
    }
    def parse(self, response):
        #print response.body
        #js = json.loads(response.body)
        #html = js['html']
        #更多request,response的内容参考：https://doc.scrapy.org/en/latest/topics/request-response.html
        #pyquery01----https://pythonhosted.org/pyquery/
        #pyquery02----http://www.cnblogs.com/shaosks/p/6845655.html
        html = response.body

        jobs_pq = pq(html)

        jobs = jobs_pq.css(".job-list")

        host = 'https://www.zhipin.com'

         #初始化redis
        pool= redis.ConnectionPool(host='localhost',port=6379,decode_responses=True)
        r=redis.Redis(connection_pool=pool)
        r.sadd('res', response.url)

        for item in jobs.items(".job-primary"):

            position_info =  item.find('.info-primary')
            detail_url = host + position_info.find('.name a').attr('href')   #工作详情
            year_edu_zone_info = position_info.find('p').html().split('<em class="vline"/>')
            position_name = position_info.find('.job-title').html() #职位名称
            salary = position_info.find('.name span.red').html() or  '' #薪资
            zone = year_edu_zone_info[0]  #工作地点
            work_year = year_edu_zone_info[1] or '不限' #工作年限
            educational = year_edu_zone_info[2] #教育程度
           
            meta = {
                "position_name":position_name,
                "salary":salary,
                "work_year":work_year,
                "educational":educational,
                "zone":zone
            }
            print '%s, %s' % ("meta is:", meta) 
            key = settings.get('REDIS_POSITION_KEY')
            print '%s, %s' % ("detail_url is:", detail_url) 
            position_id = detail_url.split("/")[-1].split('.')[0]
            print '%s, %s' % ("position_id is:", position_id) 
            if (r.sadd(key,position_id)) == 1:
                time.sleep(int(random.uniform(3, 10)))
                yield  Request(detail_url,callback=self.parse_item,meta=meta)

        if self.current_page < self.max_page:
            self.current_page += 1
            api_url = "https://www.zhipin.com/c101010100/?query=php"+"&page="+str(self.current_page)
            time.sleep(int(random.uniform(3,7)))
            yield  Request(api_url,callback=self.parse)
        pass

    def parse_item(self,response):
        item = JobcrawlerItem()
        #q = response.css
        html_pq = pq(response.body)
        item['address'] = html_pq.find('.location-address').html() #address
        item['create_time'] = html_pq.find('span.time').html() #create_time
        item['body'] = html_pq('.text').html()
        item['company_name']  = html_pq('.job-sec .name').html()
        item['postion_id'] = response.url.split("/")[-1].split('.')[0]
        item = dict(item, **response.meta )
        yield  item
