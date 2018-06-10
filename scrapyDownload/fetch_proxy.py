# -*- coding: utf-8 -*-
import sys
sys.path.append("..")

print sys.path

from thrift.transport import TTransport, TSocket, TSSLSocket, THttpClient
from thrift.protocol.TBinaryProtocol import TBinaryProtocol
from thrift.protocol.TCompactProtocol import TCompactProtocol
from proxy import ProxyService
from proxy.ProxyService import ProxyQuery

import redis
from settings import PROXY_REDIS_KEY,REDIS_PORT,REDIS_SRV
import logging
from scrapyDownload.settings import PROXY_REDIS_KEY_OCC

def write_list(proxy_list):
    redis_pool = redis.ConnectionPool(host=REDIS_SRV, port=REDIS_PORT)
    r = redis.Redis(connection_pool=redis_pool)
    #proxy_list=['http://localhost:3128']
    try:
        r.delete(PROXY_REDIS_KEY)
        for proxy in proxy_list:
            proxy_str='http://%s:%d'%(proxy.ip,proxy.port)
            print proxy_str
            #如果没有被占用，推送到可用
            if r.sismember(PROXY_REDIS_KEY_OCC,proxy_str)==False:
                r.sadd(PROXY_REDIS_KEY,proxy_str)
                logging.info("put proxy %s"%(proxy_str))
    except:
        logging.error("proxy push error ")

if __name__=='__main__':
    
    host='localhost'
    #host='192.168.124.89'
    port = 9527
    
    socket = TSocket.TSocket(host, port)
    transport = TTransport.TFramedTransport(socket)
    
    protocol = TCompactProtocol(transport)

    client = ProxyService.Client(protocol)
    transport.open()
    #proxy_list=client.getProxyList(ProxyQuery(maxNumber=3000))
    proxy_list=client.getProxyList(ProxyQuery(maxNumber=300))
    
    write_list(proxy_list)
    
    transport.close()
