# -*- coding: utf-8 -*-

import scrapy
from scrapyDownload.settings import *
from scrapy.http.request.form import FormRequest
import random
from scrapy.http.response.text import TextResponse
import js2py
import re
import redis
import time
from pymongo import MongoClient
import logging
import numpy as np
import sys
import urllib
import codecs
import time


class PushManagerList():
    name='pushManagerList'

    def __init__(self,query_file):
        self.query_file=query_file
        self.redis_pool = redis.ConnectionPool(host=REDIS_SRV, port=REDIS_PORT)

#     def push_proxy(self):
#         r = redis.Redis(connection_pool=self.redis_pool)
#         proxy_list=['http://localhost:3128']
#         try:
#             for proxy in proxy_list:
#                 r.sadd(PROXY_REDIS_KEY,proxy)
#                 logging.info("put proxy %s"%(proxy))
#         except:
#             logging.error("proxy push error ")

    def push_task(self):
        r = redis.Redis(connection_pool=self.redis_pool)
        query_list=open(query_file).read().split('\n')
        
        try:
            for query in query_list:
                query=query.strip()
                if query.startswith('#') or query=='':
                    continue
                r.sadd(QUERY_REDIS_KEY,query)
                logging.info("put query %s"%(query))
        except:
            logging.error("query push error ")


if __name__=='__main__':
#     if len(sys.argv)!=1:
#         print 'python put_task.py <query_file>'
#         sys.exit(1)
    
    #query_file=sys.argv[1]
    #关键词查询
    #query_file='/home/lipeng/workspace/scrapyDownload/query_file'
    #行政案由
    #query_file='/home/lipeng/workspace/scrapyDownload/query_file.xzay.run'
    #案由
    #query_file='/home/lipeng/workspace/scrapyDownload/query_file.msay.run'
    #地区
    query_file='/home/lipeng/workspace/scrapyDownload/query_file.loc.run'
    
    manager=PushManagerList(query_file)
    manager.push_task()
    
#     manager.push_proxy()
    
