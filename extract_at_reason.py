# -*- coding: utf-8 -*-
import re
import sys
from bs4 import BeautifulSoup
import logging

def extract_by_regex(ifile,ofile):
    prefix="三级案由"
    cont=open(ifile).read()
    print cont
    #pat=r'([\(]?[\u4e00-\u9fa5\-]+[\)]?)+(\(\d+\))'
    
    pat=r'([^<>]+)\((\d+)\)'
    
    lst=re.findall(pat, cont)
    fout=open(ofile,'w')
    
    for name in lst:
        fout.write('%s:%s\t%s\n'%(prefix,name[0],name[1]))
    
    fout.close()

def extract_text(cond_map,block,fout,node_visited_map,gen_prefix=None):
    li_list=block.find_all("li")
    
    for li in li_list:
        liid=li['id']
        
            
        sub_list=li.find_all("li")
        if len(sub_list)>=1:
            extract_text(cond_map, li, fout,node_visited_map,gen_prefix)
        else:
            if node_visited_map.has_key(liid)==True:
                continue
            print liid
            print '\n!!!write ',li
            print '\n'
            
            logging.debug(cond_map[int(li['aria-level'])])
            #print prefix
            text=li.get_text()
            m=re.search(r'(.+)\((\d+)\)', text)
            query=m.group(1)
            size=m.group(2)
            
            logging.debug(query)
            logging.debug(size)
            
            prefix=gen_prefix(query)
            
            if gen_prefix is gen_prefix_by_ay:
                fout.write('%s%s'%(cond_map[int(li['aria-level'])],prefix))
            else:
                fout.write('%s:'%(prefix))
            
            
            fout.write(query.encode('utf8'))
            fout.write('\t')
            fout.write(size)
            fout.write('\n')
            
            node_visited_map[liid]=True
        
def extract_by_dom(ifile,ofile,gen_prefix=None):
        
    cond_map={2:"二",3:"三",4:"四",5:"五",6:"六"}
    
    node_visited_map={}
    
    fout=open(ofile,'w')
    lines=open(ifile).readlines()
    for line in lines:
        line=line.strip()
        if line=='':
            continue 
        
        block = BeautifulSoup(line)
        
        extract_text(cond_map, block, fout, node_visited_map, gen_prefix)
#         sys.exit(1)
            #print '%s%s%s'%(cond_map[int(li['aria-level'])],prefix,query)#%s\t%s,query,size)
            
    fout.close()   
#         sys.exit(1)
    

def gen_prefix_by_loc(query):
    print query
    if query.find("中级".decode("utf8"))!=-1:
        prefix="中级法院"
    else:
        prefix="基层法院"
    
    return prefix
    
def gen_prefix_by_ay(query):    
    prefix="级案由:"
    return prefix

    

if __name__=='__main__':
    if len(sys.argv)!=4:
        print 'python extract_at_reason <ifile> <ofile> <prefix>'
        sys.exit(1)
        
    ifile=sys.argv[1]
    ofile=sys.argv[2]
    prefix_func_str=sys.argv[3]
    
    try:
        prefix_func=globals().get(prefix_func_str)
    except Exception,e:
        prefix_func=None
    
    ## python extract_at_reason.py query_file.msay query_file.msay.run dd
    ## python extract_at_reason.py query_file.xsay query_file.xsay.run gen_prefix_by_ay
    ## python extract_at_reason.py query_file.loc query_file.loc.run gen_prefix_by_loc  
    extract_by_dom(ifile,ofile,prefix_func)

    ## python extract_at_reason.py query_file.xzay query_file.xzay.run '三级案由'
    #extract_by_regex(ifile,ofile)
