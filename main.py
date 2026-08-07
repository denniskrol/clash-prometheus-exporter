from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
import os
import requests
import time
import uvicorn

load_dotenv()

subscription_info_updated_at = None
subscription_info = None

app = FastAPI()
@app.get('/metrics', response_class=PlainTextResponse)
def index():
    all_proxies = get_proxies()
    result = ''

    proxy_statusus = get_proxies_status(all_proxies)

    result = result + '# HELP proxy_online Online proxies\n'
    result = result + '# TYPE proxy_online gauge\n'
    for proxy in proxy_statusus:
        result = result + 'proxy_online{proxy=\"' + proxy[0] + '\"} ' + str(proxy[1]) + '\n'
    result = result + '\n'

    proxy_latencies = get_proxy_latencies(all_proxies, proxy_statusus)

    result = result + '# HELP proxy_latency Latency in ms\n'
    result = result + '# TYPE proxy_latency gauge\n'
    for proxy in proxy_latencies:
        result = result + 'proxy_latency{proxy=\"' + proxy[0] + '\"} ' + str(proxy[1]) + '\n'
    result = result + '\n'

    get_subscription_info()
    global subscription_info
    if isinstance(subscription_info, list):
        result = result + '# HELP data Data in bytes\n'
        result = result + '# TYPE data gauge\n'
        result = result + 'data{type=\"upload\"} ' + str(subscription_info[0][1]) + '\n'
        result = result + 'data{type=\"download\"} ' + str(subscription_info[1][1]) + '\n'
        result = result + 'data{type=\"total\"} ' + str(subscription_info[2][1]) + '\n'
        result = result + 'data{type=\"available\"} ' + str((int(subscription_info[2][1]) - int(subscription_info[1][1]) - int(subscription_info[0][1]))) + '\n'
        result = result + '\n'

        result = result + '# HELP expires_at Expiry date in unixtime\n'
        result = result + '# TYPE expires_at gauge\n'
        result = result + 'expires_at ' + str(subscription_info[3][1]) + '\n'

    return result


def get_proxies():
    headers = {'Authorization': 'Bearer ' + os.getenv('CLASH_API_KEY')}
    response = requests.get('http://' + os.getenv('CLASH_HOST') + ':' + os.getenv('CLASH_PORT') + '/proxies/', headers=headers)

    return response.json()


def get_proxies_status(proxies):
    excluded_keys = ['Auto', 'COMPATIBLE', 'DIRECT', 'FINAL', 'GLOBAL', 'Hijacking', 'PASS', 'PROXY', 'REJECT', 'REJECT-DROP', '剩余流量', '套餐到期', '当前网址', '流量重置']
    proxy_statusus = []
    for key in proxies['proxies']:
        add_proxy = False
        if key not in excluded_keys:
            add_proxy = True
            for excluded_key in excluded_keys:
                if key.startswith(excluded_key):
                    add_proxy = False
        if add_proxy:
            proxy_statusus.append([key, int(proxies['proxies'][key]['alive'])])

    return proxy_statusus


def get_proxy_latencies(proxies, proxy_statusus):
    proxy_latencies = []
    for proxy in proxy_statusus:
        if proxy[1] == 1:
            proxy_latencies.append([proxy[0], proxies['proxies'][proxy[0]]['history'][-1]['delay']])

    return proxy_latencies


def get_subscription_info():
    if os.getenv('SUBSCRIPTION_URL') is None:
        return None

    global subscription_info_updated_at
    global subscription_info

    if subscription_info_updated_at is not None and (time.time() - subscription_info_updated_at) < 3600:
        return subscription_info

    subscription_info_updated_at = int(time.time())

    response = requests.get(os.getenv('SUBSCRIPTION_URL'))
    if response.status_code != 200:
        return None

    subscription_info_header = response.headers.get('subscription-userinfo')
    subscription_info_items = [item.strip() for item in subscription_info_header.split(";")]

    subscription_info = []
    for info in subscription_info_items:
        key, value = info.split("=")
        subscription_info.append((key, value))

    return subscription_info


if __name__ == '__main__':
    uvicorn.run(app, host=os.getenv('HTTP_HOST'), port=int(os.getenv('HTTP_PORT')), access_log=False)

