#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
@Author         : Maoyu
@LastEditTime   : 2022/04/22
@Description    : Kokomi 后端数据接口(python 备用版本)
@GitHub         : https://github.com/SangonomiyaKoko
'''
import uvicorn
from fastapi import FastAPI
import httpx
import json
import threading
import asyncio
from datetime import date, timedelta
import os
from enum import Enum


class server_enum(str, Enum):
    asia = 'asia'
    eu = 'eu'
    na = 'na'
    ru = 'ru'
    cn = 'cn'


app = FastAPI(title='Kokomi API', version='1.0.1')
file_path = os.path.dirname(__file__)


@app.get("/test/", summary='Test network connectivity', description='No description here', tags=['Data Interface'])
async def ship_info():
    return 'ok'


@app.get("/user/", summary='Test network connectivity', description='No description here', tags=['Data Interface'])
async def ship_info(aid: int, server: server_enum, use_ac: False, ac: None):
    return {'aid': aid, 'server': server, 'use_ac': use_ac}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8001)
