import urllib.request

HOST = 'http://127.0.0.1:8080'
paths = ['/', '/login', '/public/register', '/caseworker/applications']

for p in paths:
    url = HOST + p
    try:
        with urllib.request.urlopen(url, timeout=5) as r:
            status = r.getcode()
            body = r.read(1024).decode('utf-8', errors='ignore')
            snippet = '\n'.join(body.splitlines()[:5])
            print(f"{p} -> {status}\n{snippet}\n---\n")
    except Exception as e:
        print(f"{p} -> ERROR: {e}\n---\n")
