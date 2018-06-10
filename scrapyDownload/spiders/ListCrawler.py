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

class ListCrawler(scrapy.Spider):
    name='ListCrawler'
    """
    qfile: 查询所在的文件，只能包含一个查询
    使用的redis 查询结构：
    name_dup_doc_set：　文档去重
    name_fail_pageno_set：　失败页
    name_pageno_ptr：　采集页指针
    
    作用：使用proxy执行query采集，
    　　自动加载　历史已采集docId，进行去重
    
    　　所有页执行结束，将query从任务队中移除，相关去重结构删除，退出；
    　　出错次数超过　MAX_FAIL_EXIT，设置query以及proxy，退出；
    　
    """
    def __init__(self, query=None, proxy=None, maxPage=None, *args, **kwargs):
        
        print query 
        self.headers=HEADER

        self.num_per_page=NUM_PER_PAGE
        
        self.redis_pool = redis.ConnectionPool(host=REDIS_SRV, port=REDIS_PORT)  
        self.db_conn=MongoClient(MONGO_SRV,MONGO_PORT)
        #self.db=self.db_conn.dblist
        #self.db=self.db_conn.dblist2
        self.db=self.db_conn.dblist3
        
        self.prop_fail_ratio=0.2 # 以20%概率执行 name_fail_pageno_set 中的任务
        
        self.pageno=-1
        self.next_pageno=-1
    
    
        #从scrapy 参数中获得query, -a query='关键词:赔偿金_文书类型:判决书'
        #self.query = codecs.open(qfile,encoding='utf8').read()
        self.query=query.strip()
        #self.query='关键词:赔偿金_文书类型:判决书'
        if self.query.strip()=='':
            logging.info("empty query!")
            sys.exit(1)

        ##查询名作为表名
        self.table=self.db[self.query.decode('utf8')]
        
        self.name_dup_doc_set='docId_success[%s]'%(self.query)
        self.name_fail_pageno_set='pageno_fail[%s]'%(self.query) #采集失败的页
        self.name_pageno_ptr='pageno_ptr[%s]'%(self.query)  #当前采集到的页数，下次执行从该位置开始

        self.origin='http://wenshu.court.gov.cn/'
        self.start_url=self.origin+'list/list/?sorttype=1'+self.generate_url_sufix()
        
        print self.start_url
        
        self.list_url=self.origin+'List/ListContent'
        self.code_url=self.origin+'ValiCode/GetCode'

        ### proxy
        
        self.proxy=proxy
        self.fail_count=0
        
        self.maxPage=MAX_PAGE_LIST
        
        if maxPage is not None:
            maxPage=int(maxPage)
            if maxPage<MAX_PAGE_LIST:
                logging.debug("specified maxPage:%d ;"%(maxPage))
                self.maxPage=maxPage

    
    def generate_url_sufix(self):
        #&conditions=searchWord+%E5%88%A4%E5%86%B3%E4%B9%A6+++%E6%96%87%E4%B9%A6%E7%B1%BB%E5%9E%8B:%E5%88%A4%E5%86%B3%E4%B9%A6
        condition_str=''
        cond_list=re.split(r'_',self.query)
        for cond in cond_list:
            field,val=cond.split(':')
            field=urllib.quote(field.strip())
            val=urllib.quote(val.strip())
             
            cond='+++%s:%s'%(field,val) 
             
            condition_str+='&conditions=searchWord+%s'%(val)
            condition_str+=cond
             
        return condition_str
    
    def generate_post_param(self):
        return ','.join([cond.strip() for cond in re.split(r'_',self.query)])
    
#     def generate_url_sufix(self):
#         condition_str=''
#         field,val=self.query.split(':')
#         
#         field=urllib.quote(field.strip())
#         val=urllib.quote(val.strip())
#         
#         cond='+++%s:%s'%(field,val) 
#              
#         condition_str+='&conditions=searchWord+%s'%(val)
#         condition_str+=cond
#         
#         return condition_str
    
    # start_request --> do_get_code --> do_list
    #
    def start_requests(self):
        try:
            r = redis.Redis(connection_pool=self.redis_pool)
            r.sadd(PROXY_REDIS_KEY_OCC,self.proxy)
            
            yield self.proxy_request(scrapy.Request(self.start_url,headers=self.headers,callback=self.iterate_list))
        
        except Exception,e:
            self.exit_and_set(is_proxy=False,is_query=True)


    def prepare_guid(self):
        ## Lawyee.CPWSW.List.js 中的createGuid()
        def get_guid():
            jscode="""
                var createGuid = function () {
                    return (((1 + Math.random()) * 0x10000) | 0).toString(16).substring(1);
                }
                var guid1 = createGuid() + createGuid() + "-" + createGuid() + "-" + createGuid() + createGuid() + "-" + createGuid() + createGuid() + createGuid()
            """
            context = js2py.EvalJs()
            context.execute(jscode)

            return context.guid1
#             str16=hex(int((1 + random.uniform(0,1)) * 0x10000) | 0)
#             return str16[0]
        
        return get_guid()
        ## 
    
    def iterate_list(self, response):
        try:
            vjkl5_str=response.headers.getlist('Set-Cookie')[0]
            self.vjkl5=vjkl5_str.split(';')[0].split('=')[1].strip()
            self.mainBody=response.body.decode(response.encoding)
            self.fetch_next_page()
            
        except Exception,e:
            self.exit_and_set(is_proxy=False,is_query=True)
            
        return self.do_get_code(response)
        
    def do_get_code(self, response):
        """
        Lawyee.CPWSW.List.js: 
        $.ajax({
                 url: "/ValiCode/GetCode", type: "POST", async: false,
                 data: { "guid": guid1 },
                 success: function (data) {
                     yzm1 = data;
                 }
            });
        """
        try:
            updateHeaders=self.headers.copy()
            updateHeaders['Referer']=self.start_url
            updateHeaders['Origin']=self.origin
            
            self.guid=self.prepare_guid()
            #print self.vjkl5
            
            logging.debug('vjkl5:%s'%(self.vjkl5))
            logging.debug('guid:%s'%(self.guid)) 
            #logging.debug('mainbody:%s'%self.mainBody)
            
            logging.debug('pageno: %d'%(self.pageno))
            
            
            yield self.proxy_request(FormRequest(url=self.code_url,method="POST",headers=updateHeaders,
                               formdata={'guid':self.guid},
                               callback=self.do_list))
            
        except Exception,e:
            self.exit_and_set(is_proxy=False,is_query=True)

        
    def proxy_request(self,request):
        request.meta['retry_times']=1
        request.meta['proxy']=self.proxy
        return request
    
        
    def do_list(self,response):
        def getKeyFunc():
            #idx1=self.mainBody.find('var _fxxx')
	    idx1=self.mainBody.find('function getKey()')
            idx2=self.mainBody.rfind('</script>')
            

            #print self.mainBody[idx1:idx2]

	    #sys.exit(1)

            #md5=open('../md5js','r').read()
            md5=open('../js/md5.js','r').read()
            base64=open('../js/base64.js','r').read()
            sha1=open('../js/sha1.js','r').read()
            lawye=open('../js/Lawyee.CPWSW.Common.js','r').read()

            flag_list=[1,1,1,1]
            js_list=[md5,base64,sha1,lawye]
            
            cont=''
            for idx in range(len(flag_list)):
                flag=flag_list[idx]
                if flag==1:
                    cont+='\n'+js_list[idx]
                    #md5+"\n"+base64+'\n'+sha1+"\n"+lawye
            cont+='\n'
            cont+=self.mainBody[idx1:idx2]
            
            #open('/tmp/js','w').write(cont).close()
            #cont=self.mainBody[idx1:idx2]+'\n'+md5
            #print cont
            return cont

        def runJSFunc(jscode):
            """
            getkey
            """
            jscode+="\nfunction getCookie(xx){return '%s'}"%(self.vjkl5)
            #print 'aaa'
            #print jscode
            import sys
            sys.setrecursionlimit(100000)
              
            context = js2py.EvalJs()
            context.execute(jscode)

            return context.getKey()
                   
        
        def getvkey(): 
            jscode=runJSFunc(getKeyFunc())
            return jscode
        
        try:
            self.number=response.body.decode(response.encoding)
            vkey=getvkey()
            param=self.generate_post_param()
            formdata={
                'Param':param,
                #'Param':'文书类型:判决书',
                'Index':'%d'%(self.pageno),
                'Page':'%d'%(self.num_per_page),
                'Order':'法院层级',
                'Direction':'asc',
                'guid':self.guid,
                'number':self.number,
                'vl5x': vkey
            }
            
            logging.debug(formdata)
            updateHeaders=self.headers.copy()
            updateHeaders['Referer']=self.start_url
            updateHeaders['Origin']=self.origin
            
            yield self.proxy_request(FormRequest(url=self.list_url,method="POST",headers=updateHeaders,
                               formdata=formdata,
                               callback=self.after_list))
            
        except Exception,e:
            logging.error(e)
            self.exit_and_set(is_proxy=False,is_query=True)
        
        
    def fetch_from_fail_set(self):
        r = redis.Redis(connection_pool=self.redis_pool)
        try:
            pval=r.spop(self.name_fail_pageno_set)
            if pval is not None:
                self.pageno=int(pval)
                return True
        except:
            logging.error("fetch_next_page error ")

        return False
    
    def fetch_next_page(self):
        set_next_page=True
        
        if self.pageno==-1:
            try:
                r = redis.Redis(connection_pool=self.redis_pool)
                try:
                    self.pageno=int(r.get(self.name_pageno_ptr))
                except Exception, e:
                    self.pageno=np.max([int(k) for k in r.smembers(self.name_fail_pageno_set)])
                    set_next_page=False
            except:
                self.pageno=1
                
        else:
            rd=random.uniform(0,1)
            ##　从失败队列中取
            if rd<self.prop_fail_ratio:
                if self.fetch_from_fail_set()==True:
                    return 
            
            r = redis.Redis(connection_pool=self.redis_pool)
            self.pageno=int(r.get(self.name_pageno_ptr))
            
        ### 
        if self.pageno>self.maxPage:
            if self.fetch_from_fail_set()==False:
                logging.info("Task exec over %s"%(self.query))
                self.clean_key()
                self.exit_and_set(is_proxy=True,is_query=False)
        else:
            if set_next_page==True:
                ## 设置下一次要采的页
                try:
                    r = redis.Redis(connection_pool=self.redis_pool)
                    r.set(self.name_pageno_ptr,self.pageno+1)
                except Exception, e:
                    logging.error(e)            
            
        
        
        
    def after_list(self,response):
        try:
            self.write_doc(response.text)
        except:
            logging.error("failed pageno: %d"%(self.pageno))
            try:
                r = redis.Redis(connection_pool=self.redis_pool)
                r.sadd(self.name_fail_pageno_set,self.pageno)
                logging.error("SAVED failed pageno : %d"%(self.pageno))
                self.fail_count+=1
                
                """
                采集连续超过　MAX_FAIL_EXIT　失败，退出执行
                """
                if self.fail_count>MAX_FAIL_EXIT:
                    logging.info("FAIL exceeds %d"%(MAX_FAIL_EXIT))
                    self.exit_and_set(is_proxy=False,is_query=True)
                    
            except Exception, e:
                print e

        self.fetch_next_page()
        return self.do_get_code(response)
        
    def write_doc(self,text):
        jscode="datalist = eval(\"(\" + %s + \")\");" %(text)
        
        r = redis.Redis(connection_pool=self.redis_pool)  
        
        context = js2py.EvalJs()
        context.execute(jscode)
        datalist=context.datalist
        
        for k in range(len(datalist)):
            if k<1:
                continue 
            doc=datalist[k].to_dict()
            #logging.debug(doc)
            logging.debug(type(doc))
            
            if doc.has_key(DUP_ID)==True:
                docId=doc[DUP_ID]
                logging.debug('#### dedup %s'%(docId))
                
                #去重结构初始化
                self.dedup_init()
                                
                if r.sismember(self.name_dup_doc_set, docId)==False:  
                    ### write doc
                    self.table.insert(doc)
                    r.sadd(self.name_dup_doc_set,docId)
            else:
                self.table.insert(doc)
    
    
    def clean_key(self):
        r = redis.Redis(connection_pool=self.redis_pool)

        r.delete(self.name_dup_doc_set)
        r.delete(self.name_fail_pageno_set)
        r.delete(self.name_pageno_ptr)
    
    def exit_and_set(self,is_proxy,is_query):
        r = redis.Redis(connection_pool=self.redis_pool)
        
        #self.query="%s\t%s"%(self.query,self.maxPage*NUM_PER_PAGE)
        
        if is_query:
            #logging.debug("reset query %s"%(self.query))
            logging.debug("reset query %s"%("%s\t%s"%(self.query,self.maxPage*NUM_PER_PAGE)))
            r.sadd(QUERY_REDIS_KEY,"%s\t%s"%(self.query,self.maxPage*NUM_PER_PAGE))
        
        #解除占用
        r.srem(PROXY_REDIS_KEY_OCC,self.proxy)
        if is_proxy:
            logging.debug("reset proxy %s"%(self.proxy))
            r.sadd(PROXY_REDIS_KEY,self.proxy)
        
        sys.exit(1)
        
    
    def dedup_init(self):
        """
        去重结构初始化
        """
        r = redis.Redis(connection_pool=self.redis_pool)
        if r.exists(self.name_dup_doc_set)==False:
            rec_list=self.table.find({},{DUP_ID:1})
            for rec in rec_list:
                docId=rec[DUP_ID]
                r.sadd(self.name_dup_doc_set,docId)
            
            
        
    
    
