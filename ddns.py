import time
import requests

def get_current_public_ip():
    try:
        session = requests.Session()
        session.trust_env = False
        response = session.get('https://api64.ipify.org?format=json')
        if response.status_code != 200:
            print(f'Status code error: {response.content}')
            return None
        data = response.json()
        current_public_ip = data.get('ip')
        print(f'Current public IP: {current_public_ip}')
        return current_public_ip
    except Exception as e:
        print(e)
        return None

def get_cloudflare_ip(zone_identifier, domain, read_api_key):
    try:
        url = f'https://api.cloudflare.com/client/v4/zones/{zone_identifier}/dns_records'
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {read_api_key}',
        }
        params = {
            'zone_name': domain,
            'type': 'A'
        }
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            print(f'Status code error: {response.content}')
            return None
        data = response.json()
        if not data.get('success', ''):
            print(f'Failed to retrieve: {data}')
            return None
        return data.get('result', [])
    except Exception as e:
        print(e)
        return None

def update_dns_record(zone_identifier, record, update_api_key, current_public_ip):
    try:
        url = f'https://api.cloudflare.com/client/v4/zones/{zone_identifier}/dns_records/{record["id"]}'
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {update_api_key}',
        }
        body = {
            'content': f'{current_public_ip}',
            'name': f'{record["name"]}',
            'type': 'A'
        }
        response = requests.put(url, headers=headers, json=body)
        if response.status_code != 200:
            print(f'Status code error: {response.content}')
            return False
        data = response.json()
        if not data.get('success', ''):
            print(f'Update failed: {data}')
            return False
        print(f'Update successful: {data}')
        return True
    except Exception as e:
        print(e)
        return False
    
def start(zone_identifier, domain, update_api_key, read_api_key):
    last_check_timestamp = 0
    cloudflare_records = {}
    update_required = False
    while True:
        current_timestamp = time.time()
        if (current_timestamp - last_check_timestamp >= 1800) or update_required or (not cloudflare_records):
            cloudflare_records = get_cloudflare_ip(zone_identifier, domain, read_api_key)
            print(f'{cloudflare_records}')
            update_required = False
            last_check_timestamp = current_timestamp
        current_public_ip = get_current_public_ip()
        if current_public_ip:
            for record in cloudflare_records:
                record_ip = record.get('content')
                if record_ip == current_public_ip:
                    continue
                update_dns_record(zone_identifier, record, update_api_key, current_public_ip)
                update_required = True
        else:
            print('Failed to retrieve current public IP')
        time.sleep(30)

if __name__ == '__main__':
    import configparser
    config = configparser.ConfigParser()
    config.read('config.ini')

    zone_identifier = config.get('cloudflare', 'zone_identifier')
    domain = config.get('cloudflare', 'domain')
    update_api_key = config.get('cloudflare', 'update_api_key')
    read_api_key = config.get('cloudflare', 'read_api_key')

    start(zone_identifier, domain, update_api_key, read_api_key)