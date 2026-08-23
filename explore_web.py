import httpx, re
r = httpx.get('http://192.168.162.20/', timeout=5)
links = re.findall(r'href="([^"]+)"', r.text)
print('Semua link:')
for l in links:
    print(' ', l)