# -*- coding: utf-8 -*-
from scrapy import cmdline
import sys
from settings import *
import redis
import time
import subprocess 
import logging

crawler_name = 'ContCrawler'

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


def main_control():
    redis_pool = redis.ConnectionPool(host=REDIS_SRV, port=REDIS_PORT)
    r = redis.Redis(connection_pool=redis_pool)
    crawl_process_list=[]
    
    
    while True:
        new_crawl_process_list,num_live_proc=max_crawl_process(crawl_process_list)
        
        if num_live_proc>=MAX_CRAWL_PROCESS:
            time.sleep(SLEEP_SPAN)
            continue
        
        #proxy='http://localhost:3128'
        proxy=r.spop(PROXY_REDIS_KEY)
        isproxy=(proxy is not None)
        
        if isproxy:
            cmd = "scrapy crawl {0}  -a proxy={1}".format(crawler_name,proxy)
            print cmd
            #cmd = "scrapy crawl {0} -h ".format(name,query)
            child=subprocess.Popen(cmd,shell=True)
            crawl_process_list.append(child)
        else:
            logging.info('proxy is None')
            time.sleep(SLEEP_SPAN)



if __name__=='__main__':
    main_control()
#     query='/home/lipeng/workspace/scrapyDownload/ifile'
#     cmd = "scrapy crawl {0}  -a qfile={1} ".format(crawler_name,query)
#     print cmd
#     #cmd = "scrapy crawl {0} -h ".format(name,query)
#     
#     cmdline.execute(cmd.split())

    # crawler_name = 'ContCrawler'
    # proxy='http://localhost:3128'
    # # 参数不能添加引号'或者"
    # cmd = "scrapy crawl {0}  -a proxy={1}".format(crawler_name,proxy)
    # print cmd
       
    # cmdline.execute(cmd.split())

