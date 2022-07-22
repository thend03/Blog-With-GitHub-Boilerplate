# -*- coding: utf-8 -*-
"""博客构建配置文件
"""

# For Maverick
site_prefix = "/"
source_dir = "../src/"
build_dir = "../dist/"
index_page_size = 10
archives_page_size = 20
template = {
    "name": "Kepler",
    "type": "git",
    "url": "https://github.com/AlanDecode/Maverick-Theme-Kepler.git",
    "branch": "latest"
}
enable_jsdelivr = {
    "enabled": True,
    "repo": "thend03/blog-maverick@gh-pages"
}

# 站点设置
site_name = "thend03's blog"
site_logo = "${static_prefix}logo.png"
site_build_date = "2022-05-09T21:33+08:00"
author = "thend03"
email = "thend03@163.com"
author_homepage = "https://www.thend03.com"
description = "宝宝宝"
key_words = ['Maverick', 'thend03', 'Galileo', 'blog']
language = 'zh-CN'
external_links = [
    {
        "name": "maverick",
        "url": "https://github.com/thend03/blog-maverick",
        "brief": "🏄‍ Go My Own Way."
    },
    {
        "name": "thend03",
        "url": "https://blog.thend03.com",
        "brief": "thend03的博客"
    }
]
nav = [
    {
        "name": "首页",
        "url": "${site_prefix}",
        "target": "_self"
    },
    {
        "name": "归档",
        "url": "${site_prefix}archives/",
        "target": "_self"
    },
    {
        "name": "关于",
        "url": "${site_prefix}about/",
        "target": "_self"
    }
]

social_links = [
    {
        "name": "Twitter",
        "url": "https://twitter.com/AlanDecode",
        "icon": "gi gi-twitter"
    },
    {
        "name": "GitHub",
        "url": "https://github.com/AlanDecode",
        "icon": "gi gi-github"
    },
    {
        "name": "Weibo",
        "url": "https://weibo.com/5245109677/",
        "icon": "gi gi-weibo"
    }
]

head_addon = r'''
<meta http-equiv="x-dns-prefetch-control" content="on">
<link rel="dns-prefetch" href="//cdn.jsdelivr.net" />
'''

footer_addon = ''

body_addon = ''
