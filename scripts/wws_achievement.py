import httpx
import json
import os
from httpx import TimeoutException, ConnectTimeout
import logging
import asyncio
import threading
import gc
from zh_cn import lang_zh_cn
from data_source import (
    server_list,
    useless_index_list,
    useful_index_list
)
file_path = os.path.dirname(os.path.dirname(__file__))

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
[ac]
-构造url
http://vortex.worldofwarships.{}/api/accounts/{}/
http://vortex.worldofwarships.{}/api/accounts/{}/achievements/
http://vortex.worldofwarships.{}/api/accounts/{}/clans/
-返回数据结构:
{
'status':'ok/error',
'message':'SUCCESS',
'data':{
    'hidden':False,
    'name':xxxxxx,
    'dog_tag':{...}
    'achievements':{
        ......
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
        f'{server_list[server]}/api/accounts/{aid}/achievements/' +
        (f'?ac={ac}' if use_ac else ''),
        f'{server_list[server]}/api/accounts/{aid}/clans/',
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
        result['dog_tag'] = temp_data['data'][aid]['dog_tag']
    if index == 0:
        # 写入
        if 'hidden_profile' in temp_data['data'][aid]:
            result['hidden'] == True
        else:
            result['data']['user'] = temp_data['data'][aid]['statistics']['basic']
    elif index == 1:
        if 'hidden_profile' in temp_data['data'][aid]:
            result['hidden'] == True
        else:
            if result['status'] != 'ok':
                return None
            result['data']['achievements'] = temp_data['data'][aid]['statistics']['achievements']
    elif index == 2:
        result['data']['clans'] = temp_data['data']
    return result


def del_useless_index(
    json_data: dict
) -> dict:
    '''
    删除无用数据条目
    '''
    if json_data == {}:
        return json_data
    temp_res_data = {}
    for index in useful_index_list:
        temp_res_data[index] = json_data[index]
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


def get_achievements_data(
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
            'dog_tag': {},
            'data': {
                'user': {},
                'achievements': {},
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
        for index in range(0, 3):
            thread.append(threading.Thread(target=_data_processing,
                                           args=(index, aid, url_list[index],)))
        for t in thread:
            t.start()
        for t in thread:
            t.join()
        gc.collect()
        return result
    except Exception as e:
        logging.critical(f"程序内部错误,错误类型:{str(e)}")
        return {'status': 'error', 'message': '程序内部错误,请联系麻麻解决'}


# a = get_achievements_data(aid='2023619512', server='asia')

# with open('temp.json', 'w', encoding='utf-8') as f:
#     f.write(json.dumps(a, ensure_ascii=False))
# f.close()
