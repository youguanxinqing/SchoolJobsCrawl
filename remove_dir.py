# -*- coding: utf-8 -*-

"""
@Version : Python3.6
@Time    : 2018/9/16 8:11
@File    : remove_file.py
@SoftWare: PyCharm 
@Author  : Guan
@Contact : youguanxinqing@163.com
@Desc    :
=================================
    删除指定目录
=================================
"""
import shutil

def remove_dir(dir):
    """删除是定目录"""
    shutil.rmtree(dir)

if __name__ == "__main__":
    remove_dir("data")