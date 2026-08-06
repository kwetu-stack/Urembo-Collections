import requests
from urllib.parse import urljoin
base='https://web-production-2a6d6.up.railway.app'
s = requests.Session()
s.get(urljoin(base,'/login'), timeout=30)
resp = s.post(urljoin(base,'/login'), data={'username':'joyce','password':'joyce123'}, timeout=30, allow_redirects=True)
resp = s.get(urljoin(base,'/email/sync'), timeout=60, allow_redirects=True)
text = resp.text
print('status', resp.status_code)
for line in text.splitlines():
    if 'Imported' in line or 'Skipped' in line or 'Errors' in line or 'Messages Found' in line or 'success' in line.lower() or 'failed' in line.lower():
        print(line.strip())
