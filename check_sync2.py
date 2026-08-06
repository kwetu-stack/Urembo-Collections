import requests
from urllib.parse import urljoin
base = 'https://web-production-2a6d6.up.railway.app'
s = requests.Session()
resp = s.post(urljoin(base,'/login'), data={'username':'joyce','password':'joyce123'}, timeout=30, allow_redirects=True)
resp = s.get(urljoin(base,'/email/sync'), timeout=60, allow_redirects=True)
print('status', resp.status_code)
for line in resp.text.splitlines():
    line=line.strip()
    if any(x in line for x in ['Success','Messages Found','Downloaded','Imported','Skipped','Errors']):
        print(line)
