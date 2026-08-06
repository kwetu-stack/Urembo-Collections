import requests
from urllib.parse import urljoin
import re
base = 'https://web-production-2a6d6.up.railway.app'
s = requests.Session()
resp = s.post(urljoin(base,'/login'), data={'username':'joyce','password':'joyce123'}, timeout=30, allow_redirects=True)
resp = s.get(urljoin(base,'/email/sync'), timeout=60, allow_redirects=True)
print('status', resp.status_code)
rows = re.findall(r'<tr>\s*<th>([^<]+)</th>\s*<td>([^<]+)</td>\s*</tr>', resp.text)
for name, val in rows:
    print(f'{name}: {val}')
