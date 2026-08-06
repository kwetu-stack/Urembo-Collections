import requests
from urllib.parse import urljoin
base='https://web-production-2a6d6.up.railway.app'
s = requests.Session()
resp = s.get(urljoin(base,'/login'), timeout=30)
resp = s.post(urljoin(base,'/login'), data={'username':'joyce','password':'joyce123'}, timeout=30, allow_redirects=True)
resp = s.get(urljoin(base,'/email/sync'), timeout=60, allow_redirects=True)
with open('sync_result.html','w', encoding='utf-8') as f:
    f.write(resp.text)
print('status', resp.status_code)
print('len', len(resp.text))
