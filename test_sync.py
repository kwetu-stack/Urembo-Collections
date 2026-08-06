import requests
from urllib.parse import urljoin
base='https://web-production-2a6d6.up.railway.app'
s = requests.Session()
login_url = urljoin(base, '/login')
resp = s.get(login_url, timeout=30)
print('login page', resp.status_code)
resp = s.post(login_url, data={'username':'joyce','password':'joyce123'}, timeout=30, allow_redirects=True)
print('post login', resp.status_code)
print('url after login', resp.url)
if resp.status_code == 200 or resp.status_code == 302:
    sync_url = urljoin(base, '/email/sync')
    resp2 = s.get(sync_url, timeout=60, allow_redirects=True)
    print('sync status', resp2.status_code)
    print('sync url', resp2.url)
    print(resp2.text[:1000])
else:
    print('login failed body', resp.text[:1000])
