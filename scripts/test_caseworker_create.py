import requests
from bs4 import BeautifulSoup

BASE = 'http://127.0.0.1:8080'
ADMIN_EMAIL = 'admin@his.gov'
ADMIN_PWD = 'admin123'

s = requests.Session()
# login
r = s.post(f'{BASE}/login', data={'email': ADMIN_EMAIL, 'password': ADMIN_PWD}, allow_redirects=True)
if r.status_code not in (200, 302):
    print('Login failed', r.status_code)
    exit(1)

# create unique caseworker
import time
name = f'Test W {int(time.time())}'
email = f'testw{int(time.time())}@example.com'
resp = s.post(f'{BASE}/admin/caseworkers', data={
    'fullname': name,
    'email': email,
    'pwd': 'testpass',
    'phno': '555-0000'
})
print('/admin/caseworkers POST ->', resp.status_code)

# fetch listing
r2 = s.get(f'{BASE}/admin/caseworkers')
if r2.status_code != 200:
    print('Failed to get caseworkers listing', r2.status_code)
    exit(2)

soup = BeautifulSoup(r2.text, 'html.parser')
if email in r2.text or name in r2.text:
    print('SUCCESS: new caseworker appears in listing')
else:
    print('FAIL: new caseworker not found in listing')
