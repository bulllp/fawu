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

#匹配下面filter的表名里的记录进行全文采集
#filter_list=['案由:','关键词:'] # '基层法院'
filter_list=['基层法院']


class PushManagerDoc():
    name='pushManagerDoc'

    def __init__(self):
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
        self.db_conn=MongoClient(MONGO_SRV,MONGO_PORT)
        #self.db=self.db_conn.dblist
        #self.db=self.db_conn.dblist2
        self.db=self.db_conn.dblist3
        
        table_list=self.db.collection_names()
        
        r = redis.Redis(connection_pool=self.redis_pool)

        push_map={}
        
        for table_name in table_list: 
            if table_name==TABLE_DOC or table_name.find('system')!=-1:
                continue 

            ismatch=False
            for fsuffix in filter_list:
                if table_name.find(fsuffix.decode('utf8'))!=-1:
                    ismatch=True
                    break
            if ismatch==False:
                continue
            
            print table_name
            table = self.db.get_collection(table_name)
            rec_list=table.find({},{DUP_ID:1})
            
            for rec in rec_list:
                docId=rec[DUP_ID]
                push_map[docId]=1

        #sys.exit(1)
        print "total records: %d"%(len(push_map.keys()))
        #删除已有的table记录
        table_doc=self.db.get_collection(TABLE_DOC)
        rec_list=table_doc.find({},{DUP_ID:1})
        
        for rec in rec_list:
            docId=rec[DUP_ID]
            if push_map.has_key(docId):
                del push_map[docId]
        
    	print 'total push records: %d'%(len(push_map.keys()))
        #sys.exit(1)
        for docId in push_map.keys():
    	    #print 'push ',docId
    	    r.sadd(DOC_REDIS_KEY,docId)

if __name__=='__main__':
#     if len(sys.argv)!=1:
#         print 'python put_task.py <query_file>'
#         sys.exit(1)
    
    #query_file=sys.argv[1]
    
    manager=PushManagerDoc()
    
    #manager.push_proxy()
    manager.push_task()
    
