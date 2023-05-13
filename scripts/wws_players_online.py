import httpx
import json
import os
from httpx import TimeoutException, ConnectTimeout
import logging
import asyncio
import threading
import gc
import yaml

f = open(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.yaml'))
config_data = yaml.load(f.read(), Loader=yaml.FullLoader)
f.close()
APPLICATION_ID = config_data['ApiToken']['WargamingApiToken']


async def requset_data(
    url: str
) -> dict:
    '''
    通过httpx请求用户数据
    '''
    async with httpx.AsyncClient() as client:
        try:
            res = await client.get(url, timeout=3)
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


def construct_url() -> list:
    '''
    构造url
    '''
    return [
        f'https://api.worldoftanks.asia/wgn/servers/info/?application_id={APPLICATION_ID}&game=wows',
        f'https://api.worldoftanks.eu/wgn/servers/info/?application_id={APPLICATION_ID}&game=wows',
        f'https://api.worldoftanks.com/wgn/servers/info/?application_id={APPLICATION_ID}&game=wows'
    ]


async def data_processing(
    index: int,
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
    server_list = ['asia', 'eu', 'na']
    if temp_data['data']['status'] == 'error':
        result['data'][server_list[index]] = 'unavailable'
    else:
        result['data'][server_list[index]
                       ] = temp_data['data']['data']['wows'][0]['players_online']
    return None


def _data_processing(
    index: int,
    url: str
) -> None:
    '''
    None
    '''
    asyncio.run(data_processing(index=index, url=url))
    return None


def get_players_online() -> dict:
    '''
    采用多线程并发的方式请求数据
    '''
    try:
        global result
        result = {
            'status': 'ok',
            'message': 'SUCCESS',
            'data': {
                'asia': {},
                'na': {},
                'eu': {}
            }
        }
        url_list = construct_url()
        thread = []
        for index in range(0, 3):
            thread.append(threading.Thread(
                target=_data_processing,
                args=(index, url_list[index],
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


print(get_players_online())
