import httpx
import json
import os
from httpx import TimeoutException, ConnectTimeout
import logging
import asyncio
import threading
import gc
from .data_source import (
    server_list,
    useful_index_list
)
from .personal_rating import get_personal_rating
from .ship_data import ships_info_data

file_path = os.path.dirname(os.path.dirname(__file__))
# logging.basicConfig(
#     level=logging.INFO,
#     filename=os.path.join(file_path, 'log', 'kokomi_database_api.log'),
#     filemode="w",
#     format="[%(levelname)s]%(asctime)s - %(filename)s[line:%(lineno)d] - : [%(message)s]"
# )


'''
获取用户总数据
-请求参数:
aid,
server,
select, 示例：[[tier,],[type,],[nation,]]
[ac],
-构造url
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
        f'{server_list[server]}/api/accounts/{aid}/clans/',
    ]


async def data_processing(
    index: int,
    aid: str,
    select: list,
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
        result['dog_tag'] = temp_data['data'][aid]['dog_tag']
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
                for row in ships_info_data:
                    if row.ship_id == ship_id:
                        # 数据筛选
                        if select[0] == [] or row.ship_tier in select[0]:
                            if select[1] == [] or row.ship_type in select[1]:
                                if select[2] == [] or row.ship_nation in select[2]:
                                    if ship_id not in result['data']['ships']:
                                        result['data']['ships'][ship_id] = {
                                            'pvp': {},
                                            'pvp_solo': {},
                                            'pvp_div2': {},
                                            'pvp_div3': {},
                                            'rank_solo': {}
                                        }
                                    format_index(
                                        row.ship_id,
                                        ship_data[type_index_list[index-1]],
                                        type_index_list[index-1]
                                    )
                        break
                    else:
                        continue

    elif index == 6:
        result['data']['clans'] = temp_data['data']
    return result


def format_index(
    ship_id: str,
    json_data: dict,
    battle_type: str
) -> dict:
    '''
    数据处理并写入
    '''
    if json_data == {}:
        return None
    temp_res_data = {}
    for index in useful_index_list:
        temp_res_data[index] = json_data[index]

    pr_data = get_personal_rating(
        ship_id=ship_id,
        ship_data=[
            json_data['battles_count'],
            json_data['wins'],
            json_data['damage_dealt'],
            json_data['frags'],
        ],
        battle_type=battle_type
    )
    # select_ship 数据处理
    for index in [
        'value_battles_count',
        'personal_rating',
        'n_damage_dealt',
        'n_frags'
    ]:
        temp_res_data[index] = pr_data[index]
    result['data']['ships'][ship_id][battle_type] = temp_res_data
    # battle_type 数据处理
    if result['data']['pr']['battle_type'][battle_type] == {}:
        result['data']['pr']['battle_type'][battle_type] = {
            'battles_count': 0,
            'wins': 0,
            'damage_dealt': 0,
            'frags': 0,
            'original_exp': 0,
            'value_battles_count': 0,
            'personal_rating': 0,
            'n_damage_dealt': 0,
            'n_frags': 0
        }
    for index in [
        'battles_count',
        'wins',
        'damage_dealt',
        'frags',
        'original_exp'
    ]:
        result['data']['pr']['battle_type'][battle_type][index] += json_data[index]
    if pr_data['value_battles_count'] != 0:
        for index in [
            'value_battles_count',
            'personal_rating',
            'n_damage_dealt',
            'n_frags'
        ]:
            result['data']['pr']['battle_type'][battle_type][index] += pr_data[index]
    return None


def _data_processing(
    index: int,
    aid: str,
    select: list,
    url: str
) -> None:
    '''
    None
    '''
    asyncio.run(data_processing(index=index, aid=aid, select=select, url=url))
    return None


def get_select_ship_data(
    aid: str,
    server: str,
    select: list,
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
            'dog_tag': {},
            'data': {
                'user': {},
                'pr': {
                    'battle_type': {
                        'pvp': {},
                        'pvp_solo': {},
                        'pvp_div2': {},
                        'pvp_div3': {},
                        'rank_solo': {},
                    }
                },
                'ships': {},
                'clans': {}
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
                args=(index, aid, select, url_list[index],)
            ))
        for t in thread:
            t.start()
        for t in thread:
            t.join()
        gc.collect()
        return result
    except Exception as e:
        # logging.critical(f"程序内部错误,错误类型:{str(e)}")
        return {'status': 'error', 'message': '程序内部错误,请联系麻麻解决'}


# a = get_select_ship_data(aid='2023619512', server='asia',
#                          select=[[], ['Submarine'], []])

# with open('temp.json', 'w', encoding='utf-8') as f:
#     f.write(json.dumps(a, ensure_ascii=False))
# f.close()
