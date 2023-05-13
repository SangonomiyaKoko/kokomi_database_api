import httpx
import json
import os
from httpx import TimeoutException, ConnectTimeout
import logging
import asyncio
import threading
import gc
import gzip
from datetime import date
import time
import sqlite3
import yaml
from data_source import (
    server_list,
    recent_json_index,
    ach_json_index,
    ach_index_dict
)

file_path = os.path.dirname(os.path.dirname(__file__))
f = open(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.yaml'))
config_data = yaml.load(f.read(), Loader=yaml.FullLoader)
f.close()
DB_PATH = config_data['DatabaseConfig']['DatabasePath']

logging.basicConfig(
    level=logging.INFO,
    filename=os.path.join(file_path, 'log', 'kokomi_database_api.log'),
    filemode="w",
    format="[%(levelname)s]%(asctime)s - %(filename)s[line:%(lineno)d] - : [%(message)s]"
)


'''
获取用户总数据
-请求参数:
aid,
server,
date,
[ac]
-构造url
http://vortex.worldofwarships.{}/api/accounts/{}/{}
http://vortex.worldofwarships.{}/api/accounts/{}/ships/pvp/{}
http://vortex.worldofwarships.{}/api/accounts/{}/ships/pvp_solo/{}
http://vortex.worldofwarships.{}/api/accounts/{}/ships/pvp_div2/{}
http://vortex.worldofwarships.{}/api/accounts/{}/ships/pvp_div3/{}
http://vortex.worldofwarships.{}/api/accounts/{}/ships/rank_solo/{}
http://vortex.worldofwarships.{}/api/accounts/{}/clans/
-返回数据结构:
{
'status':'ok/error',
'message':'SUCCESS',
'data':{
    'hidden':False,
    'name':xxxxxx,
    'dog_tag':{...}
    'ships':{
        'ship_id';{'pvp': {}, 'pvp_solo': {}, 'pvp_div2': {}, 'pvp_div3': {}, 'rank_solo': {}}
    },
    'clan':{...}
}
}
gzip压缩
gzip.compress(bytes(str(res['data']), encoding='utf-8'))
gzip解压缩
eval(str(gzip.decompress(open('temp.txt', 'rb').read()), encoding="utf-8"))
'''


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


def user_db_path(
    aid: str,
    server: str
) -> str:
    '''
    返回用户db文件的路径
    '''
    return os.path.join(DB_PATH, f'{aid}.db')


def insert_data(
    aid: str,
    server: str,
    temp_json: json
):
    '''
    将数据插入数据库
    '''
    con = sqlite3.connect(user_db_path(aid=aid, server=server))
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


def update_today_day(
    aid: str,
    server: str,
    use_ac: bool = False,
    ac: str = None
) -> dict:
    res = update_user_data(
        aid=aid,
        server=server,
        use_ac=use_ac,
        ac=ac
    )
    if res['status'] != 'ok':
        return {'status': 'error', 'message': res['message']}
    try:
        insert_data(
            aid=aid,
            server=server,
            temp_json=res
        )
    except Exception as e:
        logging.critical(f"写入数据库错误,错误类型:{str(e)}")
        return {'status': 'error', 'message': '写入数据错误，请联系麻麻解决'}
    return {'status': 'ok', 'message': 'SUCCESS'}


def ach_decoed(
    ach_data: dict
) -> dict:
    '''
    解压缩成就数据
    '''
    temp_json = {}
    for index in ach_json_index:
        if index.index in ach_data:
            temp_json[index.keywords] = ach_data[index.index]
    return temp_json


def ships_decoed(
    ships_data: dict
) -> dict:
    '''
    解压缩船只数据
    '''
    temp_json = {}
    for ship_id, ship_data in ships_data.items():
        temp_json[ship_id] = {'pvp': {}, 'pvp_solo': {},
                              'pvp_div2': {}, 'pvp_div3': {}, 'rank_solo': {}}
        type_list = ['pvp', 'pvp_solo', 'pvp_div2', 'pvp_div3', 'rank_solo']
        for type_index in type_list:
            if ship_data == {} or ship_data[type_index] == {}:
                continue
            else:
                for index in recent_json_index:
                    temp_json[ship_id][type_index][index.keywords] = ship_data[type_index][index.index]
    return temp_json


def construct_and_decoed_data(
    row: tuple
) -> dict:
    temp = {
        'date': row[0],
        'hidden': row[1],
        'update_time': row[2],
        'last_battle_time': row[3],
        'leveling_points': row[4],
        'karma': row[5],
        'achievements': ach_decoed(eval(str(gzip.decompress(row[6]), encoding="utf-8"))),
        'ships': ships_decoed(eval(str(gzip.decompress(row[7]), encoding="utf-8")))
    }
    return temp


def read_db_data(
    aid: str,
    servre: str,
    date: str,
    today: str = date.today().strftime("%Y-%m-%d")
):
    con = sqlite3.connect(user_db_path(aid=aid, server=servre))
    cursorObj = con.cursor()
    cursorObj.execute("SELECT * FROM recent_data")
    rows = cursorObj.fetchall()
    recent_db_data = {}
    for row in rows:
        if row[0] == today:
            recent_db_data[today] = construct_and_decoed_data(row=row)
        if row[0] == date:
            recent_db_data[date] = construct_and_decoed_data(row=row)
    if date not in recent_db_data:
        return {'status': 'error', 'message': f'无当前日期数据,当前可查询{len(rows)}天'}
    with open(f'dbtest.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(recent_db_data))
    f.close()
    cursorObj.close()
    con.close()
    return {'status': 'ok', 'message': 'SUCCESS', 'data': recent_db_data}


def get_recent_data(
    aid: str,
    servre: str,
    date: str,
    today: str = date.today().strftime("%Y-%m-%d")
) -> dict:
    '''
    计算recent数据
    '''
    raw_data = read_db_data(
        aid=aid,
        servre=servre,
        date=date
    )


def ships_difference_calculation(
    new_data: dict,
    old_data: dict
) -> dict:
    '''
    计算recent差值数据
    '''
    temp_res_data = {
        'all': {},
        'pvp': {},
        'rank': {},
        'ships': []
    }
    for ship_id, ship_data


st = time.time()
print(read_db_data('2023619512', 'asia', '2023-04-21'))
print(time.time()-st)
