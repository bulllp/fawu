# fawu

本项目用于对裁判文书网的裁判文书进行采集

#### 主要功能

* 对搜索接口进行采集
* 对搜索结果文档进行采集
* 支持失败重采
* 支持多任务并发
* 支持基于代理采集
* 支持URL去重

#### 程序架构


#### 使用说明
##### 搜索结果下载


* 1 修改scrapyDownload/setting.py中的参数


    |  参数项     　　　　　　　 | 含义       |
    | ---------------------  |
    | REDIS_SRV        　　　 | Redis服务地址      |
    | REDIS_PORT             | Redis服务端口      |
    | MONGO_SRV              | mongodb服务地址    |
    | MONGO_PORT             | mongodb服务端口    |
    | PROXY_REDIS_KEY_OCC    | 已分配的代理IP在redis中的key   | 
    | PROXY_REDIS_KEY        | 可用代理IP在redis中的key      |
    | QUERY_REDIS_KEY        | 查询key      　　　|
    | DOC_REDIS_KEY          | 文档key      　　　|
    | MAX_CRAWL_PROCESS      | 并发采集进程数      |

* 2 启动mongodb
  
  ```bash sh/mongod_start.sh```

* 3 启动redis

  ```bash sh/redis_start.sh```

* 4 推送任务
 
   ```python push_list_task.py ```   
    
* 5 启动采集

   ```python run_list.py  ```

##### 文书文档下载

1-3同上

* 4 推送任务

   ```python push_list_task.py ```

* 5 启动采集

    ```python run_list.py  ```

#### 查询参数文件
query_file.xzay.run: 行政案由

query_file.msay.run: 民事案由

query_file.xsay.run: 刑事案由

