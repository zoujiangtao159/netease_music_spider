# -*- coding:utf-8 -*-
# =======================================================
# 
# @FileName  : spider.py
# @Author    : Wang Hongqing
# @Date      : 2017-04-25 18:21
# 
# =======================================================

import os
import sys
import argparse
import logging
from pymongo import MongoClient

reload(sys)
sys.setdefaultencoding('utf-8')

parser = argparse.ArgumentParser()
parser.add_argument("--start", default=0, type=int, help="起始页")
parser.add_argument("--end", default=100, type=int, help="终止页")
args = parser.parse_args()

logging.basicConfig(
    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
    level=logging.DEBUG,
    datefmt='%a, %d %b %Y %H:%M:%S'
)

header = {"Cookie": "U_TRS1=000000f2.a4057b91.56df9efc.36c71881; U_TRS2=000000f2.a4137b91.56df9efc.46fde13e",
          "Referer": "http://www.baidu.com",
          "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:43.0) Gecko/20100101 Firefox/43.0"}


class Mongo(object):
    def __init__(self, mongo_url="mongodb://admin:MzQyZDZjZWQ1Zjg@10.183.99.111:9428/admin", db_name="spider", collection="netease_music"):
        """
        
        :param mongo_url: 
        :param db_name: 
        :param collection: 
        """
        self.mongo_client = MongoClient(mongo_url)
        self.data_base = self.mongo_client[db_name]
        self.collection = self.data_base[collection]





class NetEaseMusicSpider(object):
    def __init__(self):
        self.base_url = 'http://music.163.com'

    def extract_data(self, play_url):
        pass


start = args.start
end = args.end
for index in range(start, end+1):
    play_url = "http://music.163.com/discover/playlist/?order=hot&cat=全部&limit=35&offset=%d" % start

