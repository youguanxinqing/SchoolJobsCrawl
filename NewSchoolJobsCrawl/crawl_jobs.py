import re
import os
import time
import requests
import functools
from itertools import chain
from lxml import etree
from urllib import parse
from pyquery import PyQuery as pq


from NewSchoolJobsCrawl.CONFIG import *


def many_tries(func=None, tries=3):
    """重复次数， 默认三次
    其他次数需要通过关键字传参生效"""
    if func is None:
        return functools.partial(many_tries, tries=tries)

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        nonlocal tries
        while tries:
            try:
                return func(*args, **kwargs)
            except requests.HTTPError:
                tries -= 1
        return None
    return wrapper


@many_tries
def get_one_html(url):
    """请求一个页面，返回请求结果"""
    response = requests.get(url, headers=HEADERS)
    response.encoding = response.apparent_encoding
    return response.text, response.url


def extract_title_url(html):
    """提取浏览页每个公司对应的详情页链接"""
    selector = etree.HTML(html)
    roots = selector.xpath("//table/tr/td[2]/a")
    for root in roots:
        url = root.xpath("./@href")[0]
        title = root.xpath("./text()")[0]
        yield title.strip(), url


def join_url(tail, base=BASE, body=BOYD):
    """拼接url"""
    url = re.sub(r"(\.\./)+", body, tail)
    return parse.urljoin(base, url)


def extract_detail_data(html):
    """提取详情页数据"""
    doc = pq(html)
    text = doc("tbody").text()
    link = doc("span:contains(附件) a").attr("href")
    return text, parse.urljoin(MAIN_URL, link)


def mkdir(companyName):
    """根据公司名字创建目录"""
    dirname = f"data/{companyName}"
    if not os.path.exists(dirname):
        os.mkdir(dirname)


def save_to_text(dirname, data):
    """保存至本地"""
    with open(f"data/{dirname}/info.txt", "w", encoding="utf-8") as file:
        file.write(data)


def download_doc(dirname, url, referer):
    """下载对应的doc文档
    目录名，doc的url，详情页的url"""
    if url is None:
        return

    headers = {"Referer": referer}
    headers.update(HEADERS)
    try:
        response = requests.get(url, headers=headers)
    except requests.HTTPError:
        pass
    except requests.exceptions.ConnectionError:
        print(f"【链接错误】{referer}")
    else:
        # 二进制文件需要wb
        with open("data/{}/招聘简章.doc".format(dirname), "wb") as file:
            file.write(response.content)


def init():
    """初始化配置"""
    curDir = os.path.dirname(__file__)
    dataDir = f"{curDir}/data"
    if not os.path.exists(dataDir):
        os.mkdir(dataDir)


if __name__ == "__main__":
    start = time.time()
    init()
    # fstring python3.7特性
    suffix = (f"/{i}" for i in range(1, 23))
    for page in chain([""], suffix):
        # 构建url
        url = re.sub(r".htm", str(page)+".htm", MAIN_URL)
        html, __ = get_one_html(url)
        if html:
            for title, url in extract_title_url(html):
                # 只保留公司名
                companyName = re.split(r"（|\(|\s", title)[0]
                mkdir(companyName)
                # 详情页面，详情页链接
                detailHtml, curUrl = get_one_html(join_url(url))
                # 详情页招聘信息，doc链接
                positionInfo, docLink = extract_detail_data(detailHtml)
                save_to_text(companyName, positionInfo)
                download_doc(companyName, docLink, curUrl)
                print(companyName, curUrl)

    end = time.time()
    takeTime = end - start
    print(f"【总共耗时】{takeTime}")
