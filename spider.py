# -*- coding:utf-8 -*-
# =======================================================
# 
# @FileName  : spider.py
# @Author    : Wang Hongqing
# @Date      : 2017-04-25 18:21
# 
# =======================================================

import argparse
import base64
import json
import logging
import os
import requests
import sys

from bs4 import BeautifulSoup
from pymongo import MongoClient
from Crypto.Cipher import AES
from itertools import product

reload(sys)
sys.setdefaultencoding('utf-8')

parser = argparse.ArgumentParser()
parser.add_argument("--start", default=0, type=int, help="起始页")
parser.add_argument("--end", default=10000, type=int, help="终止页")
args = parser.parse_args()

logging.basicConfig(
    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
    level=logging.INFO,
    datefmt='%a, %d %b %Y %H:%M:%S'
)


class Mongo(object):
    def __init__(self, mongo_url="mongodb://admin:MzQyZDZjZWQ1Zjg@10.183.99.111:9428/admin",
                 db_name="netease_music_spider",
                 collection="play_list"):
        """
        
        :param mongo_url: 
        :param db_name: 
        :param collection: 
        """
        self._mongo_client = MongoClient(mongo_url)
        self._data_base = self._mongo_client[db_name]
        self.collection = self._data_base[collection]

    def mongo_find(self, **kwargs):
        return self.collection.find(**kwargs)


class NetEaseMusicSpider(object):
    def __init__(self):
        self._base_url = 'http://music.163.com'
        self._mongo = Mongo(db_name="netease_music_spider", collection="play_list")
        self.header = {
            "Cookie": "U_TRS1=000000f2.a4057b91.56df9efc.36c71881; U_TRS2=000000f2.a4137b91.56df9efc.46fde13e",
            "Referer": "http://www.baidu.com",
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:43.0) Gecko/20100101 Firefox/43.0"}

    @staticmethod
    def _aesEncrypt(text, secKey):
        pad = 16 - len(text) % 16
        text = text + pad * chr(pad)
        encryptor = AES.new(secKey, 2, '0102030405060708')
        ciphertext = encryptor.encrypt(text)
        ciphertext = base64.b64encode(ciphertext)
        return ciphertext

    @staticmethod
    def _rsaEncrypt(text, pubKey, modulus):
        text = text[::-1]
        rs = int(text.encode('hex'), 16) ** int(pubKey, 16) % int(modulus, 16)
        return format(rs, 'x').zfill(256)

    @staticmethod
    def _createSecretKey(size):
        return (''.join(map(lambda xx: (hex(ord(xx))[2:]), os.urandom(size))))[0:16]

    def extract_play_link(self, play_url):
        """
        获取歌单里面的歌的链接以名字进行存储
        :param play_url: 
        :return: 
        """
        logging.info("start parsing %s" % play_url)
        # self._mongo = Mongo(db_name="netease_music_spider", collection="play_list")
        request = requests.get(play_url, headers=self.header)
        if request.status_code != 200:
            logging.error("can not get the page, exit! %s " % play_url)
            return
        soup = BeautifulSoup(request.text)
        play_lists = soup.find('ul', {'class': 'm-cvrlst f-cb'})
        if not play_lists:
            return
        for play_list in play_lists.find_all('div', {'class': 'u-cover u-cover-1'}):
            title = (play_list.find('a', {'class': 'msk'})['title']).encode("utf8")
            link = self._base_url + play_list.find('a', {'class': 'msk'})["href"]
            cnt = play_list.find('span', {'class': 'nb'}).text
            # result_dict = {"title": title, "link": link, "count": cnt}
            # if self._mongo.collection.find({"link": link}) == 0:
            #     self._mongo.collection.insert_one(result_dict)
            #     logging.info("paresd url : %s " % link)
            self.extract_song(link)

    def extract_song(self, url):
        """
        抓取歌单里面的歌曲,以及评论量
        :param url: 歌单play_list的URL
        :return: 
        """
        logging.info("start parsing %s" % url)
        self._mongo = Mongo(db_name="netease_music_spider", collection="song")
        request = requests.get(url, headers=self.header)
        if request.status_code != 200:
            logging.error("can not get the page, exit! %s " % play_url)
            return
        soup = BeautifulSoup(request.content)
        data_str = soup.find('textarea', {'style': 'display:none;'})
        music_list = json.loads(data_str.text)
        for song in music_list:
            name = song["name"].encode("utf-8")
            author = song['artists'][0]['name'].encode('utf-8')
            song_id = song["id"]
            if self._mongo.collection.find({"song_id": song_id}).count() == 0:
                result_dict = {"name": name, "author": author, "song_id": song_id}
                if self._mongo.collection.find({"song_id": song_id}).count() == 0:
                    self._mongo.collection.insert_one(result_dict)
                    self.extract_comment(song_id)

    def extract_comment(self, song_id):
        modulus = (
            "00e0b509f6259df8642dbc35662901477df22677ec152b5ff68ace615bb7b725152b3ab17a876aea8a5aa76"
            "d2e417629ec4ee341f56135fccf695280104e0312ecbda92557c93870114af6c9d05c4f7f0c3685b7a46bee"
            "255932575cce10b424d813cfe4875d3e82047b97ddef52741d546b8e289dc6935b3ece0462db0a22b8e7"
        )
        nonce = '0CoJUm6Qyw8W8jud'
        pubKey = '010001'
        text = {
            'username': '',
            'password': '',
            'rememberLogin': 'true'
        }
        text = json.dumps(text)
        secKey = self._createSecretKey(16)
        encText = self._aesEncrypt(self._aesEncrypt(text, nonce), secKey)
        encSecKey = self._rsaEncrypt(secKey, pubKey, modulus)
        data = {
            'params': encText,
            'encSecKey': encSecKey
        }
        self._mongo = Mongo(db_name="netease_music_spider", collection="song")
        url = "http://music.163.com/weapi/v1/resource/comments/R_SO_4_%d/?csrf_token=" % song_id
        request = requests.post(url, headers=self.header, data=data)
        total = request.json()["total"]
        self._mongo.collection.update_one({"song_id": song_id}, {"$set": {"comment_num": total}})


start = args.start
end = args.end
spider = NetEaseMusicSpider()
cat_list = [u"华语", u"全部"]

for item, index in product(cat_list, range(start, end + 1)):
    play_url = "http://music.163.com/discover/playlist/?order=hot&cat=%s&limit=35&offset=%d" % (item.encode("utf8"),
                                                                                                index * 35)
    try:
        spider.extract_play_link(play_url)
    except Exception, e:
        logging.error(e.message)
