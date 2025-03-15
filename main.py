from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
import os
import requests
import uvicorn

load_dotenv()

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

    return result


def get_proxies():
    headers = {'Authorization': 'Bearer ' + os.getenv('CLASH_API_KEY')}
    response = requests.get('http://' + os.getenv('CLASH_HOST') + ':' + os.getenv('CLASH_PORT') + '/proxies/', headers=headers)

    return response.json()


def get_proxies_status(proxies):
    excluded_keys = ['Auto', 'DIRECT', 'FINAL', 'GLOBAL', 'Hijacking', 'PROXY', 'REJECT']
    proxy_statusus = []
    for key in proxies['proxies']:
        if key not in excluded_keys:
            proxy_statusus.append([key, int(proxies['proxies'][key]['alive'])])

    return proxy_statusus


def get_proxy_latencies(proxies, proxy_statusus):
    proxy_latencies = []
    for proxy in proxy_statusus:
        if proxy[1] == 1:
            proxy_latencies.append([proxy[0], proxies['proxies'][proxy[0]]['history'][-1]['delay']])

    return proxy_latencies


if __name__ == '__main__':
    uvicorn.run(app, host=os.getenv('HTTP_HOST'), port=int(os.getenv('HTTP_PORT')), access_log=False)

