import requests
import asyncio
import random
import functools
import redis

global REDIS_CLIENT


def init_redis():
    pool = redis.ConnectionPool(host='192.168.160.247', port=6379,
                                db=0, password='W03wx2020@redis')
    global REDIS_CLIENT
    REDIS_CLIENT = redis.Redis(connection_pool=pool)


def close_redis():
    global REDIS_CLIENT
    REDIS_CLIENT.close()


def fake_header():
    user_agent_list = [
        'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95',
        'Safari/537.36 OPR/26.0.1656.60',
        'Opera/8.0 (Windows NT 5.1; U; en)',
        'Mozilla/5.0 (Windows NT 5.1; U; en; rv:1.8.1) Gecko/20061208 Firefox/2.0.0 Opera 9.50',
        'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:34.0) Gecko/20100101 Firefox/34.0',
        'Mozilla/5.0 (X11; U; Linux x86_64; zh-CN; rv:1.9.2.10) Gecko/20100922 Ubuntu/10.10 '
        '(maverick) Firefox/3.6.10',
        'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/39.0.2171.71 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 '
        '(KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
    ]
    UserAgent = random.choice(user_agent_list)
    header = {'User-Agent': UserAgent}
    return header


async def http_client(host):
    # 获取tle数据
    loop = asyncio.get_event_loop()
    future = loop.run_in_executor(
        None, functools.partial(requests.get, host, headers=fake_header()))
    response = await future
    if response.status_code == 200:
        # 解析tle
        list_tle = parse_tle(response.text)
        storage_tle(list_tle)
    else:
        print('down load tle error')


def storage_tle(list_tle):
    for temp in list_tle:
        # 判断两行的有效性可以再完善下此处只做了长度校验
        if len(temp) == 3:
            # 获取两行第二行noradid
            key = temp[2].split()[1]
            global REDIS_CLIENT
            REDIS_CLIENT.hset('orbit_global_tle', key, '\r\n'.join(temp))


def parse_tle(context):
    list_original = context.split('\r\n')
    # 把list分为长度为5的4段
    list_tle = []
    for i in range(0, len(list_original), 3):
        list_tle.append(list_original[i:i+3])
    return list_tle


if __name__ == "__main__":
    # 初始化redis连接
    init_redis()
    # 获取数据
    loop = asyncio.get_event_loop()
    tasks = [http_client(host)
             for host in ['https://www.celestrak.com/NORAD/elements/tle-new.txt']]
    loop.run_until_complete(asyncio.wait(tasks))
    loop.close()
    # 关闭连接
    close_redis()
