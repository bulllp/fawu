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

class ContCrawler(scrapy.Spider):
    name='ContCrawler'
    
    def __init__(self, proxy=None, *args, **kwargs):
        
        self.headers=HEADER

        self.redis_pool = redis.ConnectionPool(host=REDIS_SRV, port=REDIS_PORT)  
        self.db_conn=MongoClient(MONGO_SRV,MONGO_PORT)
        #self.db=self.db_conn.dblist
        self.db=self.db_conn.dblist3
        
        self.prop_fail_ratio=0.2 # 以20%概率执行 name_fail_pageno_set 中的任务
        
        ##cont_查询名作为表名
        self.table=self.db[TABLE_DOC]
        self.name_fail_doc_set=DOC_REDIS_KEY+'_fail'
        self.name_doc_set=DOC_REDIS_KEY

        self.origin='http://wenshu.court.gov.cn/'
        self.content_url='http://wenshu.court.gov.cn/CreateContentJS/CreateContentJS.aspx?'

        #proxy        
        self.proxy=proxy
        self.fail_count=0
    
        # 
        self.docId=None
        self.queue_name=None
        
        
    def proxy_request(self,request):
        request.meta['proxy']=self.proxy
        return request
    
    def fetch_next_doc(self):
        if self.docId is None:
            try:
                r = redis.Redis(connection_pool=self.redis_pool)
                self.docId=r.spop(self.name_doc_set)
                
                if self.docId is None:
                    self.fetch_from_fail_set()
            except:
                logging.error("no doc found at queue %s"%(self.queue_name))
                self.exit_and_set(is_proxy=False,is_query=False)
                
        else:
            rd=random.uniform(0,1)
            ##　从失败队列中取
            if rd<self.prop_fail_ratio:
                if self.fetch_from_fail_set()==True:
                    return 
            
            r = redis.Redis(connection_pool=self.redis_pool)
            self.docId=r.spop(self.name_doc_set)
        
    
    def fetch_from_fail_set(self):
        r = redis.Redis(connection_pool=self.redis_pool)
        try:
            pval=r.spop(self.name_fail_doc_set)
            if pval is not None:
                self.docId=pval
                return True
        except:
            logging.error("fetch_next_page error ")

        return False
    
    
    def start_requests(self):
        r = redis.Redis(connection_pool=self.redis_pool)

        self.fetch_next_doc()
        r.sadd(PROXY_REDIS_KEY_OCC,self.proxy)
        
        if self.docId is not None:
            self.referer_url=self.origin+'content/content?DocID=%s'%(self.docId)
            self.start_url=self.content_url+'DocID=%s'%(self.docId)
            
            updateHeaders=self.headers.copy()
            updateHeaders['Referer']=self.referer_url
#             updateHeaders['Origin']=self.origin
            yield self.proxy_request(scrapy.Request(self.start_url,headers=updateHeaders,callback=self.after_doc))
        else:
            r.srem(PROXY_REDIS_KEY_OCC,self.proxy)
    
    
    def after_doc(self,response):
        try:
            #print response.text
            self.write_doc(response.text)
        except:
            logging.error("failed doc: %s"%(self.docId))
            try:
                r = redis.Redis(connection_pool=self.redis_pool)
                r.sadd(self.name_fail_doc_set,self.docId)
                logging.error("SAVED failed doc : %s"%(self.docId))
                self.fail_count+=1
                
                """
                采集连续超过　MAX_FAIL_EXIT　失败，退出执行
                """
                if self.fail_count>MAX_FAIL_EXIT:
                    logging.info("FAIL exceeds %d"%(MAX_FAIL_EXIT))
                    self.exit_and_set(is_proxy=False,is_query=False)
                
            except Exception, e:
                print e

        return self.start_requests()
    
        
    def write_doc(self,text):
        idx1=text.find('var jsonHtmlData')
        idx2=text.find('var jsonData')
        
        block=text[idx1:idx2].strip()
        jscode=block+'var jsonData = eval("(" + jsonHtmlData + ")");'
        
        context = js2py.EvalJs()
        context.execute(jscode)
        
        doc=context.jsonData.to_dict()
        doc[DUP_ID]=self.docId
        
        logging.debug('#### save %s'%(self.docId))
        
        self.table.insert(doc)

    def exit_and_set(self,is_proxy,is_query):
        r = redis.Redis(connection_pool=self.redis_pool)
        
        #解除占用
        r.srem(PROXY_REDIS_KEY_OCC,self.proxy)
        if is_proxy==False:
            logging.debug("remove proxy %s"%(self.proxy))
            r.srem(PROXY_REDIS_KEY,self.proxy)
        
        sys.exit(1)
        
if __name__=='__main__':
    jscode=codecs.open('../../def',encoding='utf8').read()
    
    context = js2py.EvalJs()
    context.execute(jscode)

    print context.jsonData.to_dict()
    print type(context.jsonData.to_dict())
