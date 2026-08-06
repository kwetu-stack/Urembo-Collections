import requests
from urllib.parse import urljoin
import re
base = 'https://web-production-2a6d6.up.railway.app'
s = requests.Session()
resp = s.post(urljoin(base,'/login'), data={'username':'joyce','password':'joyce123'}, timeout=30, allow_redirects=True)
resp = s.get(urljoin(base,'/email/messages'), timeout=60, allow_redirects=True)
rows = re.findall(r'<tr>.*?<td>\s*(\d+)\s*</td>.*?<span class="badge bg-success">\s*([^<]+)\s*</span>.*?<td>\s*(.*?)\s*</td>.*?\n.*?<td>\s*(.*?)\s*</td>.*?\n.*?<td>\s*(.*?)\s*</td>', resp.text, re.S)
print('rows', len(rows))
for idx, kind, attachment, date, sender in rows[:30]:
    print(idx, kind.strip(), attachment.strip(), date.strip(), sender.strip())
