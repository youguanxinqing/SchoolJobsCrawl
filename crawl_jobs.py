# -*- coding: utf-8 -*-

"""
@Version : Python3.6
@Time    : 2018/9/15 18:13
@File    : process.py
@SoftWare: PyCharm 
@Author  : Guan
@Contact : youguanxinqing@163.com
@Desc    :
=================================
    爬取学校校招信息
=================================
"""
import os
import time
import requests
from pyquery import PyQuery as pq
from collections import namedtuple
from itertools import chain
from urllib import parse
from lxml import etree
from urllib import error
from CONFIG import *

def get_one_html(url, tries=3):
    """获取一个网页"""
    try:
        response = requests.get(url, headers=HEADERS)
    except error.HTTPError:
        if tries <= 0:
            return None
        else:
            get_one_html(url, tries-1)
    else:
        response.encoding = response.apparent_encoding

        bag.html = response.text
        bag.url = response.url
        return bag

def extract_html(html):
    """提取网页内容"""
    selector = etree.HTML(html)
    roots = selector.xpath('//div[@id="vsb_content"]//tbody/tr')
    for root in roots[1:]:
        company = root.xpath("./td[1]/text()")
        time = root.xpath("./td[2]/text()")
        position = root.xpath("./td[3]/text()")
        link = root.xpath("./td[4]/a/@href")

        yield {
            "company": "".join(company),
            "time": "".join(time),
            "position": "".join(position),
            "link": "".join(link),
        }

def extract_detail_html(bag):
    """提取详情页内容"""
    doc = pq(bag.html)
    data = doc("#vsb_content_100 tr").text()
    # 文本信息
    result = map(lambda x: x.replace("\n", ":"), [item for item in data.split(" ") if item])
    # 招聘简章链接
    link = doc(".Main tr td span > a").attr("href")
    return (result, parse.urljoin(bag.url, link))

def save_to_txt(dirname, url, data):
    """将数据保存到txt文件中
    目录名，详情页url, 详情页内容"""
    with open("data/{}/详情.txt".format(dirname), "w", encoding="utf-8") as file:
        for item in chain([url], data):
            file.write("{0}\n{1}\n".format(item, "-"*50))

def download_doc(dirname, url, referer):
    """下载对应的doc文档
    目录名，doc的url，详情页的url"""
    headers = {"Referer": referer}
    headers.update(HEADERS)
    try:
        response = requests.get(url, headers=headers)
    except error.HTTPError:
        pass
    else:
        # 二进制文件需要wb
        with open("data/{}/招聘简章.doc".format(dirname), "wb") as file:
            file.write(response.content)

def init():
    """初始化配置"""
    path = "data".format(os.path.dirname(__file__))
    if not os.path.exists(path):
        os.mkdir(path)

if __name__ == "__main__":
    start = time.time()
    init()
    bag = namedtuple("html_link", ["html", "url"])

    html = get_one_html(JOBS_URL).html
    if html:
        for item in extract_html(html):
            detail = get_one_html(item["link"])
            if detail:
                # 以公司名创建文件夹
                if not os.path.exists("data/{}".format(item["company"])):
                    os.mkdir("data/{}".format(item["company"]))
                data, link = extract_detail_html(detail)
                save_to_txt(item["company"], detail.url, data)
                download_doc(item["company"], link, detail.url)
                print(item["company"], link)
    else:
        print("[request dir html failure]")

    end = time.time() - start
    # 打印程序耗时
    print("take time: {}".format(end))