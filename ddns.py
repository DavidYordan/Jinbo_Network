import time
import requests

def get_current_public_ip():
    try:
        session = requests.Session()
        session.trust_env = False
        response = session.get('https://api64.ipify.org?format=json')
        if response.status_code != 200:
            print(f'状态码错误:{response.content}')
            return None
        data = response.json()
        current_ip = data.get('ip')
        print(f'当前公网IP:{current_ip}')
        return current_ip
    except Exception as e:
        print(e)
        return None

def get_cloudflare_ip(zone_identifier, domain, read_key):
    try:
        url = f'https://api.cloudflare.com/client/v4/zones/{zone_identifier}/dns_records'
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {read_key}',
        }
        params = {
            'zone_name': domain,
            'type': 'A'
        }
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            print(f'状态码错误:{response.content}')
            return None
        data = response.json()
        if not data.get('success', ''):
            print(f'获取失败:{data}')
            return None
        return data.get('result', [])
    except Exception as e:
        print(e)
        return None

def update_dns_record(zone_identifier, item, update_key, current_ip):
    try:
        url = f'https://api.cloudflare.com/client/v4/zones/{zone_identifier}/dns_records/{item["id"]}'
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {update_key}',
        }
        body = {
            'content': f'{current_ip}',
            'name': f'{item["name"]}',
            'type': 'A'
        }
        response = requests.put(url, headers=headers, json=body)
        if response.status_code != 200:
            print(f'状态码错误:{response.content}')
            return False
        data = response.json()
        if not data.get('success', ''):
            print(f'更新失败:{data}')
            return False
        print(f'更新成功:{data}')
        return True
    except Exception as e:
        print(e)
        return False
    
def start(zone_identifier, domain, update_key, read_key):
    last_check_time = 0
    cloudflare_info = {}
    update_sign = False
    while True:
        current_time = time.time()
        if (current_time - last_check_time >= 1800) or update_sign or (not cloudflare_info):
            cloudflare_info = get_cloudflare_ip(zone_identifier, domain, read_key)
            print(f'{cloudflare_info}')
            update_sign = False
            last_check_time = current_time
        current_ip = get_current_public_ip()
        if current_ip:
            for item in cloudflare_info:
                item_ip = item.get('content', '')
                if item_ip == current_ip:
                    continue
                update_dns_record(zone_identifier, item, update_key, current_ip)
                update_sign = True
        else:
            print('获取当前公网IP失败')
        time.sleep(30)

if __name__ == '__main__':
    import configparser
    config = configparser.ConfigParser()
    config.read('config.ini')

    zone_identifier = config.get('cloudflare', 'zone_identifier')
    domain = config.get('cloudflare', 'domain')
    update_key = config.get('cloudflare', 'update_key')
    read_key = config.get('cloudflare', 'read_key')

    start(zone_identifier, domain, update_key, read_key)