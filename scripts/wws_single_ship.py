import httpx
import json
import os
from httpx import TimeoutException, ConnectTimeout
import logging
import asyncio
import threading
import gc
import yaml
from data_source import (
    server_list,
    api_server_list,
    useful_index_list
)
from personal_rating import get_personal_rating

file_path = os.path.dirname(os.path.dirname(__file__))
f = open(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.yaml'))
config_data = yaml.load(f.read(), Loader=yaml.FullLoader)
f.close()
APPLICATION_ID = config_data['ApiToken']['WargamingApiToken']
LATESTSEASON = config_data['WargamingConfig']['LatestRankSeason']

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
ship_id,
[ac]
-构造url
http://vortex.worldofwarships.{}/api/accounts/{}/ships/pvp/{}
http://vortex.worldofwarships.{}/api/accounts/{}/ships/pvp_solo/{}
http://vortex.worldofwarships.{}/api/accounts/{}/ships/pvp_div2/{}
http://vortex.worldofwarships.{}/api/accounts/{}/ships/pvp_div3/{}
http://vortex.worldofwarships.{}/api/accounts/{}/ships/rank_solo/{}
https://api.worldofwarships.asia/wows/seasons/shipstats/?application_id={}&account_id={}&ship_id={}
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
                return {'status': 'ok', 'message': 'SUCCESS', 'data': result}
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
    ship_id: str,
    use_ac: bool = False,
    ac: str = None
) -> list:
    '''
    构造url
    '''
    return [
        f'{server_list[server]}/api/accounts/{aid}/' +
        (f'?ac={ac}' if use_ac else ''),
        f'{server_list[server]}/api/accounts/{aid}/ships/{ship_id}/pvp/' +
        (f'?ac={ac}' if use_ac else ''),
        f'{server_list[server]}/api/accounts/{aid}/ships/{ship_id}/pvp_solo/' +
        (f'?ac={ac}' if use_ac else ''),
        f'{server_list[server]}/api/accounts/{aid}/ships/{ship_id}/pvp_div2/' +
        (f'?ac={ac}' if use_ac else ''),
        f'{server_list[server]}/api/accounts/{aid}/ships/{ship_id}/pvp_div3/' +
        (f'?ac={ac}' if use_ac else ''),
        f'{server_list[server]}/api/accounts/{aid}/ships/{ship_id}/rank_solo/' +
        (f'?ac={ac}' if use_ac else ''),
        f'{server_list[server]}/api/accounts/{aid}/clans/',
        f'{api_server_list[server]}/wows/seasons/shipstats/?application_id={APPLICATION_ID}&account_id={aid}&ship_id={ship_id}'
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
    if temp_data['data']['status'] != 'ok':
        result['status'] = 'error'
        result['message'] = temp_data['data']['message']
        return None
    if index == 0:
        result['nickname'] = temp_data['data']['data'][aid]['name']
        result['dog_tag'] = temp_data['data']['data'][aid]['dog_tag']
    if index == 0:
        # 写入
        if 'hidden_profile' in temp_data['data']['data'][aid]:
            result['hidden'] == True
        else:
            result['data']['user'] = temp_data['data']['data'][aid]['statistics']['basic']
    elif (
        index >= 1
        and index <= 5
    ):
        type_index_list = ['pvp', 'pvp_solo',
                           'pvp_div2', 'pvp_div3', 'rank_solo']
        if 'hidden_profile' in temp_data['data']['data'][aid]:
            result['hidden'] == True
        else:
            for ship_id, ship_data in temp_data['data']['data'][aid]['statistics'].items():
                if result['status'] != 'ok':
                    return None
                if ship_id not in result['data']['ships']:
                    result['data']['ships'][ship_id] = {
                        'pvp': {}, 'pvp_solo': {}, 'pvp_div2': {}, 'pvp_div3': {}, 'rank_solo': {}}
                result['data']['ships'][ship_id][type_index_list[index-1]] = format_index(
                    ship_data[type_index_list[index-1]], ship_id, type_index_list[index-1])
    elif index == 6:
        result['data']['clans'] = temp_data['data']['data']
    elif index == 7:
        season_list = [str(LATESTSEASON-2),
                       str(LATESTSEASON-1), str(LATESTSEASON)]
        if temp_data['data']['meta']['hidden'] == None:
            season_data = temp_data['data']['data'][aid][0]['seasons']
            for i in season_list:
                result['data']['season'][i] = {}
                if i in season_data:
                    result['data']['season'][i] = format_season_data(
                        season_data[i]['0']['rank_solo'])
        else:
            for i in season_list:
                result['data']['season'][i] = {}
    return result


def format_season_data(
    json_data: dict
) -> dict:
    '''
    处理排位赛季数据
    '''
    temp_json = {
        'battles_count': json_data['battles'],
        'wins': json_data['wins'],
        'losses': json_data['losses'],
        'damage_dealt': json_data['damage_dealt'],
        'frags': json_data['frags'],
        'planes_killed': json_data['planes_killed'],
        'survived': json_data['survived_battles'],
        'win_and_survived': json_data['survived_wins'],
        'hits_by_main': json_data['main_battery']['hits'],
        'shots_by_main': json_data['main_battery']['shots']
    }
    return temp_json


def format_index(
    json_data: dict,
    ship_id: str,
    battle_type: str
) -> dict:
    '''
    数据条目
    '''
    if json_data == {}:
        return json_data
    temp_res_data = {}
    for index in useful_index_list:
        temp_res_data[index] = json_data[index]
    pr_data = get_personal_rating(
        ship_id=ship_id,
        ship_data=[
            temp_res_data['battles_count'],
            temp_res_data['wins'],
            temp_res_data['damage_dealt'],
            temp_res_data['frags'],
        ],
        battle_type=battle_type
    )
    for index in ['value_battles_count', 'personal_rating', 'n_damage_dealt', 'n_frags']:
        temp_res_data[index] = pr_data[index]
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


def get_single_ship_data(
    aid: str,
    server: str,
    ship_id: str,
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
                'ships': {},
                'season': {},
                'pr': {},
                'clans': {}
            }
        }
        url_list = construct_url(
            aid=aid,
            server=server,
            ship_id=ship_id,
            use_ac=use_ac,
            ac=ac
        )
        thread = []
        for index in range(0, 8):
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


a = get_single_ship_data(aid='2023619512', server='asia', ship_id='4277090288')

with open('temp.json', 'w', encoding='utf-8') as f:
    f.write(json.dumps(a, ensure_ascii=False))
f.close()
