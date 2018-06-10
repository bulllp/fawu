# -*- coding: utf-8 -*-
import js2py
import re
from pymongo import MongoClient

def getKeyFunc():
    mainBody=open('../list.html','r').read()
    idx1=mainBody.find('var _fxxx')
    idx2=mainBody.rfind('</script>')
    
    print mainBody[idx1:idx2]
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
    cont+='\n'+mainBody[idx1:idx2]
    print cont
    return cont


def runJSFunc(jscode):
    """
    getkey
    """
#     jscode+="\nfunction getCookie(xx){return '%s'}"%('vjkl5')    
    print jscode
    context = js2py.EvalJs()
    context.execute(jscode)
           
    return context.getKey()
           
#     result = js2py.eval_js(jscode) 
#     return result

def getvkey(): 
    jscode=runJSFunc(getKeyFunc())
    print jscode
     

import simplejson as json
import codecs 
def readlist():
    json_content=codecs.open('../listdoc',encoding="utf8").read()
    jscode="datalist = eval(\"(\" + %s + \")\");" %(json_content)
    
    context = js2py.EvalJs()
    context.execute(jscode)
    datalist=context.datalist
    for k in range(len(datalist)):
        if k<1:
            continue 
        doc=datalist[k]
        print doc
    
def testMongo():
    MONGO_SRV="127.0.0.1"
    MONGO_PORT=27017
    
    db_conn=MongoClient(MONGO_SRV,MONGO_PORT)
    db=db_conn.dblist
    table=db.table
    table.insert({'abc':'def','123':'456'})


import urllib
def generate_url_sufix(query):
    #&conditions=searchWord+%E5%88%A4%E5%86%B3%E4%B9%A6+++%E6%96%87%E4%B9%A6%E7%B1%BB%E5%9E%8B:%E5%88%A4%E5%86%B3%E4%B9%A6
    condition_str=''
    cond_list=re.split(r'_',query)
    for cond in cond_list:
        field,val=cond.split(':')
        v1=val #urllib.quote(val)
        v2=cond #urllib.quote(cond)
        condition_str+='&conditions=searchWord+%s'%(v1)
        condition_str+='+++%s'%(v2)
        
    return condition_str

if __name__=='__main__':
    #mainBody=open('../abc','r').read()
    #print getKeyFunc(mainBody)
    
    import sys
    sys.setrecursionlimit(1000000)  
    vkey=getvkey()
    sys.exit(1)
    
    jscode=open('../test.js','r').read()
    print jscode
    context = js2py.EvalJs()
    context.execute(jscode)
    context.getKey()
    
    #readlist()
    
    #testMongo()
    
#     query='关键词:赔偿金_文书类型:判决书'
#     print generate_url_sufix(query)
    
    
    
    