# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals
import logging

class FailErr(Exception):
    def __init__(self,val):
        self.val=val

from scrapy.exceptions import IgnoreRequest

class CustomFailMiddleware(object):
    def process_response(self, request, response, spider):
        logging.info("!!!! response_status:%d"%(response.status))
        #raise FailErr(301)
        if response.status!=200:
            spider.exit_and_set(is_proxy=False,is_query=True)
        
        return response
    
    def process_exception(self, request, exception, spider):
        spider.exit_and_set(is_proxy=False,is_query=True)


# # Importing base64 library because we'll need it ONLY in case if the proxy we are going to use requires authentication
# import base64 
# # Start your middleware class
# class ProxyMiddleware(object):
#     # overwrite process request
#     def process_request(self, request, spider):
#         # Set the location of the proxy
#         request.meta['proxy'] = spider.proxy
# #         # Use the following lines if your proxy requires authentication
# #         proxy_user_pass = "USERNAME:PASSWORD"
# #         # setup basic authentication for the proxy
# #         encoded_user_pass = base64.encodestring(proxy_user_pass)
# #         request.headers['Proxy-Authorization'] = 'Basic ' + encoded_user_pass


    

class ScrapydownloadSpiderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, dict or Item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Response, dict
        # or Item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)
