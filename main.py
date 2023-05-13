#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
@Author         : Maoyu
@LastEditTime   : 2022/04/22
@Description    : Kokomi 后端数据接口(python 版本)
@GitHub         : https://github.com/SangonomiyaKoko
'''
import uvicorn
import httpx
import json
from datetime import date, timedelta
import os
import ast
from enum import Enum
from typing import Optional
from fastapi import Depends, FastAPI

from scripts import wws_basic_data
from scripts import wws_select_ship


app = FastAPI(title='Kokomi API', version='1.0.1')
file_path = os.path.dirname(__file__)


@app.get("/test/", summary='测试', description='No description here', tags=['Test Interface'])
async def ship_info():
    return 'ok'


async def user_basic_parameters(aid: int, server: str, use_ac: bool = False, ac: str = None):
    return {
        "aid": aid,
        "server": server,
        "use_ac": use_ac,
        "ac": ac
    }


@app.get("/user/basic/", summary='用户基础数据', description='No description here', tags=['Data Interface'])
async def user_basic(commons: dict = Depends(user_basic_parameters)):
    resunt = wws_basic_data.get_user_basic_data(
        aid=str(commons['aid']),
        server=commons['server'],
        use_ac=commons['use_ac'],
        ac=commons['ac']
    )
    return resunt


async def ships_select_parameters(aid: int, server: str, select: str, use_ac: bool = False, ac: str = None):
    return {
        "aid": aid,
        "server": server,
        "select": select,
        "use_ac": use_ac,
        "ac": ac
    }


@app.get("/ships/select/", summary='用户船只数据(筛选)数据', description='No description here', tags=['Data Interface'])
async def user_basic(commons: dict = Depends(ships_select_parameters)):
    resunt = wws_select_ship.get_select_ship_data(
        aid=str(commons['aid']),
        server=commons['server'],
        select=ast.literal_eval(commons['select']),
        use_ac=commons['use_ac'],
        ac=commons['ac']
    )
    return resunt


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=1001)
