import urllib.request
import subprocess
import time
import json
import os

p = subprocess.Popen(['python', 'app.py', '8082'], cwd=r'C:\Users\USER\Desktop\pointage_arex')
time.sleep(1.5)

try:
    # 1. Test /scanner
    with urllib.request.urlopen('http://127.0.0.1:8082/scanner') as resp:
        mob_html = resp.read().decode('utf-8')
        print('/scanner Status:', resp.status, '| Length:', len(mob_html))
        assert 'Pointage Promoteur' in mob_html
        assert 'mobile-reader' in mob_html

    # 2. Test /api/agents
    with urllib.request.urlopen('http://127.0.0.1:8082/api/agents') as resp:
        agents = json.loads(resp.read().decode('utf-8'))
        print('Total agents:', len(agents))
        assert len(agents) == 68
        assert 'google_form_url' in agents[0]
        assert 'https://docs.google.com/forms' in agents[0]['google_form_url']

    print('VERIFICATION: /scanner and agents API verified 100% OK!')
finally:
    p.terminate()
