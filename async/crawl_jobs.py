import aiohttp
import asyncio
import re
import os
import time
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
            except:
                tries -= 1
        return None
    return wrapper


async def get(url, referer=None):
    """支持异步的get请求"""
    headers = HEADERS
    # 兼容下载doc文档的操作
    if referer is not None:
        # 请求头必须保证内容都是str类型
        r = {"Referer": str(referer)}
        headers.update(r)

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            text = await response.read()
            url = response.url  # 这里返回的url是URL类型
            assert response.status == 200

    return text, url


@many_tries
async def get_one_html(url):
    """请求一个页面，返回请求结果"""
    textBytes, url = await get(url)
    # 返回来的字符串是bytes类型，需要转换成str
    textStr = bytes.decode(textBytes)
    return textStr, url


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


async def save_to_text(dirname, data):
    """保存至本地"""
    with open(f"data/{dirname}/info.txt", "w", encoding="utf-8") as file:
        file.write(data)


async def download_doc(dirname, url, referer):
    """下载对应的doc文档
    目录名，doc的url，详情页的url"""
    if url is None:
        return

    try:
        content, url = await get(url, referer)
    except aiohttp.client_exceptions.ClientConnectorError:
        print(f"【失败链接】{url}")
    else:
        # 二进制文件需要wb
        with open("data/{}/招聘简章.doc".format(dirname), "wb") as file:
            file.write(content)


def init():
    """初始化配置"""
    curDir = os.path.dirname(__file__)
    dataDir = f"{curDir}/data"
    if not os.path.exists(dataDir):
        os.mkdir(dataDir)


async def main(url):
    html, __ = await get_one_html(url)
    if html:
        for title, url in extract_title_url(html):
            # 只保留公司名
            companyName = re.split(r"（|\(|\s", title)[0]
            mkdir(companyName)
            # 详情页面，详情页链接
            detailHtml, curUrl = await get_one_html(join_url(url))
            # 详情页招聘信息，doc链接
            positionInfo, docLink = extract_detail_data(detailHtml)
            await save_to_text(companyName, positionInfo)
            await download_doc(companyName, docLink, curUrl)
            print(companyName, curUrl)


if __name__ == "__main__":
    start = time.time()
    init()
    # fstring python3.7特性
    suffix = (f"/{i}" for i in range(1, 23))

    # 注意这一部分的改动
    urls = [re.sub(r".htm", str(page)+".htm", MAIN_URL) for page in chain([""], suffix)]
    tasks = [asyncio.ensure_future(main(url)) for url in urls]

    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.wait(tasks))
    loop.close()
    # --------注意线条-------------

    end = time.time()
    takeTime = end - start
    print(f"【总共耗时】{takeTime}")
