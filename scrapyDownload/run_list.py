# -*- coding: utf-8 -*-
from scrapy import cmdline
import sys
from settings import *
import redis
import time
import subprocess 
import logging
import re

crawler_name = 'ListCrawler'

def max_crawl_process(crawl_process_list):
    num_live_proc=0
    new_crawl_process_list=[]
    for child in crawl_process_list:
        ####  https://docs.python.org/3.1/library/subprocess.html#subprocess.Popen.returncode
        ####  A None value indicates that the process hasn’t terminated yet. 
        if child.poll() is None:
            num_live_proc+=1
            new_crawl_process_list.append(child)
            
    return new_crawl_process_list,num_live_proc

def escape_sh(argument):
    return '%s' % (
        argument
        .replace('\\', '\\\\')
        .replace('"', '\\"')
        .replace('$', '\\$')
        .replace('`', '\\`')
        .replace('(', '\(')
        .replace(')', '\)')
    )

def main_control():
    redis_pool = redis.ConnectionPool(host=REDIS_SRV, port=REDIS_PORT)
    r = redis.Redis(connection_pool=redis_pool)
    crawl_process_list=[]
    
    
    while True:
        new_crawl_process_list,num_live_proc=max_crawl_process(crawl_process_list)
        
        if num_live_proc>=MAX_CRAWL_PROCESS:
            time.sleep(SLEEP_SPAN)
            continue
        
        query=r.spop(QUERY_REDIS_KEY)
        isquery=(query is not None)
        
        #proxy='http://localhost:3128'
        proxy=r.spop(PROXY_REDIS_KEY)
        isproxy=(proxy is not None)
        
        if isquery and isproxy:
            arr=re.split(r'\s+',query)
            print '^^^query',query
            print '^^^arr ',arr
            
            import pipes
            query=pipes.quote(arr[0])
            maxPage=-1
            if len(arr)>1:
                try:
                    maxPage=int(arr[1])/NUM_PER_PAGE
                except Exception,e:
                    maxPage=-1
                
            cmd = "scrapy crawl {0}  -a query={1} -a proxy={2}".format(crawler_name,query,proxy)
            if maxPage!=-1:
                cmd+=' -a maxPage=%d'%(maxPage)
                
            print cmd
            print re.split(r'\s+',cmd)
#             sys.exit(1)
            #cmd = "scrapy crawl {0} -h ".format(name,query)
            child=subprocess.Popen(cmd,shell=True)
            crawl_process_list.append(child)
        else:
            if isquery==False:
                logging.info('QUERY is None')
            else:
                r.sadd(QUERY_REDIS_KEY,query)
                
            if isproxy==False:
                logging.info('proxy is None')
            else:
                r.sadd(PROXY_REDIS_KEY,proxy)
                
            time.sleep(SLEEP_SPAN)

if __name__=='__main__':
    main_control()
#     query='/home/lipeng/workspace/scrapyDownload/ifile'
#     cmd = "scrapy crawl {0}  -a qfile={1} ".format(crawler_name,query)
#     print cmd
#     #cmd = "scrapy crawl {0} -h ".format(name,query)
#     
#     cmdline.execute(cmd.split())

#    query='关键词:赔偿金_文书类型:判决书'
##     query="\'三级案由:公安行政管理-治安管理(治安)\'"
##     query='abc'
#    proxy='http://localhost:3128'
#    # 参数不能添加引号'或者"
#    cmd = "scrapy crawl {0}  -a query={1} -a proxy={2} -a maxPage=10".format(crawler_name,query,proxy)
#    print cmd
##
#    cmdline.execute(cmd.split())

