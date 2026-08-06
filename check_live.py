import requests
from urllib.parse import urljoin
base = 'https://web-production-2a6d6.up.railway.app'
s = requests.Session()
# login
resp = s.post(urljoin(base,'/login'), data={'username':'joyce','password':'joyce123'}, timeout=30, allow_redirects=True)
print('login', resp.status_code, resp.url)
# performance page
resp = s.get(urljoin(base,'/performance/'), timeout=30, allow_redirects=True)
print('performance', resp.status_code)
print(resp.text[:1200])
# sync page
resp = s.get(urljoin(base,'/email/sync'), timeout=60, allow_redirects=True)
print('sync', resp.status_code)
print(resp.text[:1200])
