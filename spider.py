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
import requests
from bs4 import BeautifulSoup

reload(sys)
sys.setdefaultencoding('utf-8')

parser = argparse.ArgumentParser()
parser.add_argument("--start", default=0, type=int, help="起始页")
parser.add_argument("--end", default=100, type=int, help="终止页")
args = parser.parse_args()

logging.basicConfig(
    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
    level=logging.INFO,
    datefmt='%a, %d %b %Y %H:%M:%S'
)

header = {"Cookie": "U_TRS1=000000f2.a4057b91.56df9efc.36c71881; U_TRS2=000000f2.a4137b91.56df9efc.46fde13e",
          "Referer": "http://www.baidu.com",
          "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:43.0) Gecko/20100101 Firefox/43.0"}


class Mongo(object):
    def __init__(self, mongo_url="mongodb://admin:MzQyZDZjZWQ1Zjg@10.183.99.111:9428/admin", db_name="netease_music_spider",
                 collection="play_list"):
        """
        
        :param mongo_url: 
        :param db_name: 
        :param collection: 
        """
        self._mongo_client = MongoClient(mongo_url)
        self._data_base = self._mongo_client[db_name]
        self._collection = self._data_base[collection]

    def mongo_insert(self, link, name, cnt):
        """
        
        :param link: 
        :param name: 
        :param cnt: 
        :return: 
        """
        if self._collection.find({"link": link}) != 0:
            self._collection.insert_one({"name": name, "link": link, "count": cnt})


class NetEaseMusicSpider(object):
    def __init__(self):
        self._base_url = 'http://music.163.com'
        self._mongo = Mongo(db_name="netease_music_spider", collection="play_list")

    def extract_song_link(self, play_url):
        """
        获取歌单里面的歌的链接以名字进行存储
        :param play_url: 
        :return: 
        """
        self._mongo = Mongo(db_name="netease_music_spider", collection="play_list")
        request = requests.get(play_url)
        if request.status_code != 200:
            logging.error("can not get the page, exit! %s " % play_url)
            return
        soup = BeautifulSoup(request.text)
        play_lists = soup.find('ul', {'class': 'm-cvrlst f-cb'})
        for play_list in play_lists.find_all('div', {'class': 'u-cover u-cover-1'}):
            title = (play_list.find('a', {'class': 'msk'})['title']).encode("utf8")
            link = self._base_url + play_list.find('a', {'class': 'msk'})["href"]
            cnt = play_list.find('span', {'class': 'nb'}).text
            self._mongo.mongo_insert(link=link, name=title, cnt=cnt)
        logging.info("paresd url : %s " % (play_url))


start = args.start
end = args.end
spider = NetEaseMusicSpider()
for index in range(start, end + 1):
    play_url = "http://music.163.com/discover/playlist/?order=hot&cat=全部&limit=35&offset=%d" % (start * 35)
    spider.extract_song_link(play_url)
