import requests
from urllib.parse import urljoin
base = 'https://web-production-2a6d6.up.railway.app'
s = requests.Session()
resp = s.post(urljoin(base,'/login'), data={'username':'joyce','password':'joyce123'}, timeout=30, allow_redirects=True)
for path in ['/agents/','/dashboard/']:
    resp=s.get(urljoin(base,path), timeout=30, allow_redirects=True)
    print(path, resp.status_code)
    if 'Total Agents' in resp.text:
        start = resp.text.find('Total Agents')
        print(resp.text[start:start+250])
    if 'Total Agents' not in resp.text:
        print('no total label')
