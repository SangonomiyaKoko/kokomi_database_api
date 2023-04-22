import json
import sqlite3
import httpx
import gzip
import time
import os
from httpx import TimeoutException, ConnectTimeout
import logging
import asyncio
import threading
import gc
from datetime import date
from data_source import (
    server_list,
    recent_json_index,
    ach_index_dict,
    ach_json_index
)

file_path = os.path.dirname(os.path.dirname(__file__))
db_path = r'E:\kokomi_database_api\database\user_db'
user_list = [('2023619512', 'asia', False, None), ]
error_list = []


async def requset_data(
    url: str
) -> dict:
    '''
    通过httpx请求用户数据
    '''
    async with httpx.AsyncClient() as client:
        try:
            res = await client.get(url, timeout=5)
            requset_code = res.status_code
            code_msg = {
                403: '数据服务器拒绝访问',
                404: '查询不到用户数据',
                500: '数据服务器内部错误',
                503: '数据服务器不可用'
            }
            result = res.json()
            if requset_code == 200:
                return {'status': 'ok', 'message': 'SUCCESS', 'data': result['data']}
            if (
                # 特殊情况处理，如用户没有添加过工会请求会返回404
                'clan' in url
                and requset_code == 404
            ):
                return {'status': 'ok', 'message': 'SUCCESS', 'data': {"role": None, "clan": {}, "joined_at": None, "clan_id": None}}
            if requset_code in code_msg:
                logging.critical(f"网路请求错误,url:{url},code:{requset_code}")
                return {'status': 'error', 'message': code_msg[requset_code]}
            else:
                logging.critical(f"网路请求错误,url:{url},code:{requset_code}")
                return {'status': 'error', 'message': '网络请求错误,请稍后重试'}
        except (TimeoutException, ConnectTimeout):
            logging.warning(f"网络请求超时,url:{url}")
            return {'status': 'error', 'message': '网络请求超时,请稍后重试'}
        except Exception as e:
            logging.critical(f"网路请求错误,url:{url},错误类型:{str(e)}")
            return {'status': 'error', 'message': '网路请求错误,请稍后重试'}


def construct_url(
    aid: str,
    server: str,
    use_ac: bool = False,
    ac: str = None
) -> list:
    '''
    构造url
    '''
    return [
        f'{server_list[server]}/api/accounts/{aid}/' +
        (f'?ac={ac}' if use_ac else ''),
        f'{server_list[server]}/api/accounts/{aid}/ships/pvp/' +
        (f'?ac={ac}' if use_ac else ''),
        f'{server_list[server]}/api/accounts/{aid}/ships/pvp_solo/' +
        (f'?ac={ac}' if use_ac else ''),
        f'{server_list[server]}/api/accounts/{aid}/ships/pvp_div2/' +
        (f'?ac={ac}' if use_ac else ''),
        f'{server_list[server]}/api/accounts/{aid}/ships/pvp_div3/' +
        (f'?ac={ac}' if use_ac else ''),
        f'{server_list[server]}/api/accounts/{aid}/ships/rank_solo/' +
        (f'?ac={ac}' if use_ac else ''),
        f'{server_list[server]}/api/accounts/{aid}/achievements/' +
        (f'?ac={ac}' if use_ac else '')
    ]


async def data_processing(
    index: int,
    aid: str,
    url: str
) -> None:
    '''
    处理请求获取的数据
    '''
    temp_data = await requset_data(url=url)
    if temp_data['status'] != 'ok':
        result['status'] = 'error'
        result['message'] = temp_data['message']
        return None
    if index == 0:
        result['nickname'] = temp_data['data'][aid]['name']
        result['update_time'] = int(time.time())
    if index == 0:
        # 写入
        if 'hidden_profile' in temp_data['data'][aid]:
            result['hidden'] == True
        else:
            result['data']['user'] = temp_data['data'][aid]['statistics']['basic']
    elif (
        index >= 1
        and index <= 5
    ):
        type_index_list = ['pvp', 'pvp_solo',
                           'pvp_div2', 'pvp_div3', 'rank_solo']
        if 'hidden_profile' in temp_data['data'][aid]:
            result['hidden'] == True
        else:
            for ship_id, ship_data in temp_data['data'][aid]['statistics'].items():
                if result['status'] != 'ok':
                    return None
                if ship_id not in result['data']['ships']:
                    result['data']['ships'][ship_id] = {
                        'pvp': {}, 'pvp_solo': {}, 'pvp_div2': {}, 'pvp_div3': {}, 'rank_solo': {}}
                result['data']['ships'][ship_id][type_index_list[index-1]] = del_useless_index(
                    ship_data[type_index_list[index-1]])
    elif index == 6:
        result['data']['achievements'] = ach_index(
            temp_data['data'][aid]['statistics']['achievements'])
    return result


def ach_index(
    json_data: dict
) -> dict:
    '''
    处理成就数据
    '''
    if json_data == {}:
        return json_data
    temp_res_data = {}
    for ach_id, ach_name in ach_index_dict.items():
        ach_id = str(ach_id)
        if ach_id in json_data:
            for index in ach_json_index:
                if index.keywords == ach_name:
                    temp_res_data[index.index] = json_data[ach_id]['count']
                else:
                    continue
        else:
            continue
    return temp_res_data


def del_useless_index(
    json_data: dict
) -> dict:
    '''
    删除无用数据条目
    '''
    if json_data == {}:
        return json_data
    temp_res_data = {}
    for index in recent_json_index:
        temp_res_data[index.index] = json_data[index.keywords]
    return temp_res_data


def _data_processing(
    index: int,
    aid: str,
    url: str
) -> None:
    '''
    None
    '''
    asyncio.run(data_processing(index=index, aid=aid, url=url))
    return None


def update_user_data(
    aid: str,
    server: str,
    use_ac: bool = False,
    ac: str = None
) -> dict:
    '''
    采用多线程并发的方式请求数据
    '''
    try:
        global result
        result = {
            'status': 'ok',
            'message': 'SUCCESS',
            'hidden': False,
            'nickname': None,
            'update_time': 0,
            'data': {
                'user': {},
                'ships': {},
                'achievements': {}
            }
        }
        url_list = construct_url(
            aid=aid,
            server=server,
            use_ac=use_ac,
            ac=ac
        )
        thread = []
        for index in range(0, 7):
            thread.append(threading.Thread(
                target=_data_processing,
                args=(index, aid, url_list[index],
                      )))
        for t in thread:
            t.start()
        for t in thread:
            t.join()
        gc.collect()
        return result
    except Exception as e:
        logging.critical(f"程序内部错误,错误类型:{str(e)}")
        return {'status': 'error', 'message': '程序内部错误,请联系麻麻解决'}


def insert_sql(
    temp_json: json
) -> str:
    '''
    sql插入语句及数据
    '''
    sql = '''INSERT INTO recent_data(
    date,
    hidden,
    update_time,
    last_battle_time,
    leveling_points,
    karma,
    achievements,
    ships
    ) VALUES(?, ?, ?,?, ?, ?, ?, ?)'''
    data = (
        date.today().strftime("%Y-%m-%d"),
        temp_json['hidden'],
        temp_json['update_time'],
        temp_json['data']['user']['last_battle_time'],
        temp_json['data']['user']['leveling_points'],
        temp_json['data']['user']['karma'],
        gzip.compress(
            bytes(str(temp_json['data']['achievements']), encoding='utf-8')),
        gzip.compress(bytes(str(temp_json['data']['ships']), encoding='utf-8')))
    return (sql, data)


def insert_data(
    aid: str,
    server: str,
    temp_json: json
):
    '''
    将数据插入数据库
    '''
    con = sqlite3.connect(os.path.join(db_path, f'{aid}.db'))
    cursorObj = con.cursor()
    sql_tuple = insert_sql(temp_json=temp_json)
    try:
        cursorObj.execute(sql_tuple[0], sql_tuple[1])
    except:
        today = date.today().strftime("%Y-%m-%d")
        cursorObj.execute(f"DELETE from recent_data where date = '{today}'")
        cursorObj.execute(sql_tuple[0], sql_tuple[1])
    con.commit()
    con.close()


def database_update(
    user_info_list: list
) -> None:
    for index in user_info_list:
        res = update_user_data(
            aid=index[0],
            server=index[1],
            use_ac=index[2],
            ac=index[3]
        )
        if res['status'] != 'ok':
            error_list.append(index)
            continue
        try:
            insert_data(
                aid=index[0],
                server=index[1],
                temp_json=res
            )
        except Exception as e:
            logging.critical(f"写入数据库错误,错误类型:{str(e)}")
            error_list.append(index)


database_update(user_list)


# a = update_user_data(aid='2023619512', server='asia')

# with open('temp3.json', 'w', encoding='utf-8') as f:
#     f.write(json.dumps(a, ensure_ascii=False))
# f.close()
