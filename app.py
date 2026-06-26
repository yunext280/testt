import os, re, json, time, threading
from flask import Flask, jsonify, request, abort, Response
import requests as req
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

app = Flask(__name__)
ext_port = os.environ.get('FLASK_EXT_PORT', '5001')
device_ua = None
last_result_title = ''
last_result_body = ''

chrome_options = Options()
chrome_options.add_argument('--headless=new')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--disable-blink-features=AutomationControlled')
chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
chrome_options.add_experimental_option('useAutomationExtension', False)
chrome_options.binary_location = '/usr/bin/chromium'
chrome_service = Service(executable_path='/usr/bin/chromedriver')

def get_driver():
    opts = Options()
    for arg in chrome_options.arguments:
        opts.add_argument(arg)
    for k, v in chrome_options.experimental_options.items():
        opts.add_experimental_option(k, v)
    opts.binary_location = chrome_options.binary_location
    if device_ua:
        opts.add_argument(f'--user-agent={device_ua}')
    driver = webdriver.Chrome(service=chrome_service, options=opts)
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': 'Object.defineProperty(navigator,"webdriver",{get:()=>undefined})'
    })
    return driver

@app.before_request
def before_req():
    global device_ua
    ua = request.headers.get('User-Agent')
    if ua:
        device_ua = ua
    token = request.args.get('token') or request.headers.get('X-Exclusive-Token')
    if token != 'MyPrivateAppToken_98765':
        abort(403)

@app.route('/')
def home():
    init_title = last_result_title or ''
    init_body = last_result_body or 'Click a button to start'
    import html
    escaped_body = html.escape(init_body)
    return f'''<!DOCTYPE html>
<html><head><meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>UBBN Scraper</title>
<style>body{{font-family:sans-serif;padding:16px;background:#111;color:#eee;max-width:600px;margin:auto}}
button{{background:#2a7;color:#fff;border:0;padding:10px 20px;border-radius:6px;font-size:16px;margin:4px;cursor:pointer}}
input{{width:100%;padding:8px;margin:8px 0;background:#222;border:1px solid #444;color:#eee;border-radius:4px;box-sizing:border-box}}
pre{{background:#222;padding:12px;border-radius:6px;overflow:auto;font-size:13px;white-space:pre-wrap}}
</style></head><body>
<h2>UBBN Scraper</h2>
<p style="color:#888">Port: {ext_port} | UA: {(device_ua or '...')}</p>
<h3>Light Scrape (requests + BS4)</h3>
<input id="url_light" value="https://google.com"/>
<button onclick="scrape('light')">Scrape Light</button>
<h3>Full Scrape (Selenium)</h3>
<input id="url_selenium" value="https://google.com"/>
<button onclick="scrape('selenium')">Scrape Selenium</button>
<h3>Posts</h3>
<button onclick="getPosts()">Get Posts from earning-bot.eu.org</button>
<div id="result_title" style="margin:8px 0;font-weight:bold">{init_title}</div>
<pre id="output">{escaped_body}</pre>
<script>
const TOKEN='MyPrivateAppToken_98765';
async function scrape(mode){{
  const url=document.getElementById('url_'+mode).value;
  const o=document.getElementById('output');
  const t=document.getElementById('result_title');
  o.textContent='Loading...';
  t.textContent='';
  try{{
    const r=await fetch('/scrape?url='+encodeURIComponent(url)+'&mode='+mode+'&token='+TOKEN);
    const d=await r.json();
    if(d.status=='ok'){{
      t.textContent='Title: '+(d.data.title||'(no title)');
      const content=mode=='selenium'?d.data.html:d.data.text;
      o.textContent=content||'(empty)';
    }}else{{
      o.textContent='Error: '+(d.message||'unknown');
    }}
  }}catch(e){{o.textContent='Error: '+e}}
}}
async function getPosts(){{
  const o=document.getElementById('output');
  const t=document.getElementById('result_title');
  o.textContent='Loading posts...';
  t.textContent='';
  try{{
    const r=await fetch('/posts?token='+TOKEN);
    const d=await r.json();
    if(d.status=='ok'){{
      t.textContent='Found '+d.data.length+' posts';
      o.textContent=d.data.map((p,i)=>'\\n'+((i+1)+'. ')+p.title+'\\n   '+p.link).join('');
    }}else{{
      o.textContent='Error: '+(d.message||'unknown');
    }}
  }}catch(e){{o.textContent='Error: '+e}}
}}
</script></body></html>'''

@app.route('/status')
def status():
    return jsonify(status='ok')

@app.route('/posts')
def posts():
    global last_result_title, last_result_body
    try:
        driver = get_driver()
        driver.get('https://www.earning-bot.eu.org/')
        time.sleep(3)
        items = []
        for a in driver.find_elements(By.TAG_NAME, 'a'):
            href = a.get_attribute('href')
            txt = a.text.strip()
            if href and txt and not href.startswith('javascript'):
                items.append({'title': txt, 'link': href})
        driver.quit()
        seen = set()
        unique = []
        for it in items:
            if it['link'] not in seen:
                seen.add(it['link']); unique.append(it)
        last_result_title = f'Found {len(unique)} posts'
        last_result_body = '\n'.join(f'{i+1}. {p["title"]}\n   {p["link"]}' for i, p in enumerate(unique))
        return jsonify(status='ok', data=unique)
    except Exception as e:
        last_result_title = 'Error'
        last_result_body = str(e)
        return jsonify(status='error', message=str(e))

@app.route('/scrape')
def scrape():
    global last_result_title, last_result_body
    url = request.args.get('url', 'https://google.com')
    mode = request.args.get('mode', 'light')
    try:
        if mode == 'selenium':
            driver = get_driver()
            driver.get(url)
            time.sleep(2)
            result = {'title': driver.title, 'html': driver.page_source[:5000]}
            driver.quit()
        else:
            resp = req.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
            soup = BeautifulSoup(resp.text, 'html.parser')
            result = {'title': soup.title.string if soup.title else '', 'text': soup.get_text()[:2000]}
        last_result_title = 'Title: ' + (result['title'] or '(no title)')
        last_result_body = (result.get('html') or result.get('text') or '(empty)')[:5000]
        return jsonify(status='ok', data=result)
    except Exception as e:
        last_result_title = 'Error'
        last_result_body = str(e)
        return jsonify(status='error', message=str(e))

@app.route('/set_cookies', methods=['POST'])
def set_cookies():
    site = request.args.get('site', 'unknown')
    cookies = request.get_json()
    path = os.path.expanduser('~/cookies_' + site + '.json')
    with open(path, 'w') as f:
        json.dump(cookies, f)
    os.makedirs(os.path.expanduser('~/screenshots'), exist_ok=True)
    t = threading.Thread(target=capture_screenshot, args=(site,))
    t.start()
    return jsonify(status='ok')

@app.route('/test_cookies', methods=['POST'])
def test_cookies():
    site = request.args.get('site', 'all')
    os.makedirs(os.path.expanduser('~/screenshots'), exist_ok=True)
    sites = ['aviso', 'youtube'] if site == 'all' else [site]
    threads = []
    for s in sites:
        cookie_file = os.path.expanduser('~/cookies_' + s + '.json')
        if os.path.exists(cookie_file):
            t = threading.Thread(target=capture_screenshot, args=(s,))
            t.start()
            threads.append(t)
    for t in threads:
        t.join()
    return jsonify(status='ok', tested=sites)

def capture_screenshot(site):
    try:
        driver = get_driver()
        urls = {'aviso': 'https://aviso.bz', 'youtube': 'https://m.youtube.com'}
        url = urls.get(site, 'https://google.com')
        cookie_file = os.path.expanduser('~/cookies_' + site + '.json')
        if os.path.exists(cookie_file):
            with open(cookie_file) as f:
                cookies = json.load(f)
            driver.get(url)
            for c in cookies:
                try:
                    driver.add_cookie(c)
                except:
                    pass
            driver.get(url)
            time.sleep(3)
        else:
            driver.get(url)
            time.sleep(2)
        driver.save_screenshot(os.path.expanduser('~/screenshots/' + site + '_login.png'))
        driver.quit()
    except Exception as e:
        print('Screenshot failed for', site, ':', e)
        try:
            driver.quit()
        except:
            pass

@app.route('/screenshots/<name>')
def screenshot(name):
    path = os.path.expanduser('~/screenshots/' + name)
    if not os.path.exists(path):
        abort(404)
    with open(path, 'rb') as f:
        return Response(f.read(), mimetype='image/png')

@app.route('/aviso')
def aviso():
    import html
    token = request.args.get('token', '')
    aviso_step = request.args.get('aviso_step', '')
    yt_step = request.args.get('yt_step', '')
    ss_dir = os.path.expanduser('~/screenshots')
    aviso_ok = os.path.exists(os.path.expanduser('~/cookies_aviso.json'))
    yt_ok = os.path.exists(os.path.expanduser('~/cookies_youtube.json'))
    aviso_time = time.ctime(os.path.getmtime(os.path.expanduser('~/cookies_aviso.json'))) if aviso_ok else ''
    yt_time = time.ctime(os.path.getmtime(os.path.expanduser('~/cookies_youtube.json'))) if yt_ok else ''
    ss_aviso = '/screenshots/aviso_login.png?token=' + token if os.path.exists(os.path.join(ss_dir, 'aviso_login.png')) else ''
    ss_yt = '/screenshots/youtube_login.png?token=' + token if os.path.exists(os.path.join(ss_dir, 'youtube_login.png')) else ''
    ss_aviso_time = time.ctime(os.path.getmtime(os.path.join(ss_dir, 'aviso_login.png'))) if ss_aviso else ''
    ss_yt_time = time.ctime(os.path.getmtime(os.path.join(ss_dir, 'youtube_login.png'))) if ss_yt else ''
    aviso_img = '<br><img src="' + ss_aviso + '" style="max-width:280px;border:1px solid #555;border-radius:4px"><br><small style="color:#888">' + ss_aviso_time + '</small>' if ss_aviso else ''
    yt_img = '<br><img src="' + ss_yt + '" style="max-width:280px;border:1px solid #555;border-radius:4px"><br><small style="color:#888">' + ss_yt_time + '</small>' if ss_yt else ''
    aviso_color = '#0f0' if aviso_ok else '#666'
    yt_color = '#0f0' if yt_ok else '#666'
    aviso_mark = '\u2714' if aviso_ok else '\u2718'
    yt_mark = '\u2714' if yt_ok else '\u2718'

    if aviso_step == 'fail':
        aviso_card_click = 'onclick="Android.verifyAviso()"'
        aviso_card_cls = 'card card-clickable'
        aviso_msg = '<p style="color:#f55;margin:4px 0">Not logged in. Please sign in and try again.</p>'
    elif aviso_step == 'check':
        aviso_card_click = ''
        aviso_card_cls = 'card'
        aviso_msg = '<p style="color:#aaa;margin:4px 0">Click Done to save cookies</p>'
    elif aviso_ok:
        aviso_card_click = ''
        aviso_card_cls = 'card'
        aviso_msg = ''
    else:
        aviso_card_click = 'onclick="Android.verifyAviso()"'
        aviso_card_cls = 'card card-clickable'
        aviso_msg = ''

    aviso_btn = ('<button class="btn-done" onclick="Android.doneAviso()">Done</button>' if aviso_step == 'check' else '')
    aviso_test = '<button class="btn-test" onclick="testSite(\'aviso\')"' + (' disabled' if not aviso_ok else '') + '>Test</button>'
    aviso_time_str = '<br><small style="color:#888">saved: ' + aviso_time + '</small>' if aviso_time else ''

    if yt_step == 'fail':
        yt_card_click = 'onclick="Android.verifyYoutube()"'
        yt_card_cls = 'card card-clickable'
        yt_msg = '<p style="color:#f55;margin:4px 0">Not logged in. Please sign in and try again.</p>'
    elif yt_step == 'avatar_ok':
        yt_card_click = 'onclick="Android.verifyYoutubeSubscribe()"'
        yt_card_cls = 'card card-clickable'
        yt_msg = '<p style="color:#aaa;margin:4px 0">Check if subscribed to @mmrid07</p>'
    elif yt_step == 'not_subscribed':
        yt_card_click = 'onclick="Android.verifyYoutubeSubscribe()"'
        yt_card_cls = 'card card-clickable'
        yt_msg = '<p style="color:#f55;margin:4px 0">Not subscribed yet. Subscribe and try again.</p>'
    elif yt_step == 'subscribed':
        yt_card_click = ''
        yt_card_cls = 'card'
        yt_msg = '<p style="color:#aaa;margin:4px 0">Click Done to save cookies</p>'
    elif yt_ok:
        yt_card_click = ''
        yt_card_cls = 'card'
        yt_msg = ''
    else:
        yt_card_click = 'onclick="Android.verifyYoutube()"'
        yt_card_cls = 'card card-clickable'
        yt_msg = ''

    yt_btn = ('<button class="btn-done" onclick="Android.doneYoutube()">Done</button>' if yt_step == 'subscribed' else '')
    yt_test = '<button class="btn-test" onclick="testSite(\'youtube\')"' + (' disabled' if not yt_ok else '') + '>Test</button>'
    yt_time_str = '<br><small style="color:#888">saved: ' + yt_time + '</small>' if yt_time else ''

    p = '<!DOCTYPE html><html><head><meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/><title>Setup</title>'
    p += '<style>body{font-family:sans-serif;padding:16px;background:#111;color:#eee;max-width:600px;margin:auto}.card{background:#222;padding:16px;border-radius:8px;margin:12px 0}.card-clickable{cursor:pointer}.card-clickable:hover{background:#2a2a2a}.btn{background:#2a7;color:#fff;border:0;padding:10px 20px;border-radius:6px;font-size:16px;margin:4px;cursor:pointer;text-decoration:none;display:inline-block}.btn:disabled,.btn-test:disabled{opacity:0.4;cursor:default}.btn-done{background:#27a;color:#fff;border:0;padding:10px 20px;border-radius:6px;font-size:16px;margin:4px;cursor:pointer;text-decoration:none;display:inline-block}.btn-test{background:#a50;color:#fff;border:0;padding:8px 16px;border-radius:6px;font-size:14px;margin:4px;cursor:pointer;text-decoration:none;display:inline-block}.loading{color:#aaa;text-align:center;display:none;margin:8px 0}</style></head><body><h2>Setup</h2>'
    p += '<div class="' + aviso_card_cls + '" ' + aviso_card_click + '><h3>Aviso.bz <span style="color:' + aviso_color + '">' + aviso_mark + '</span></h3>' + aviso_time_str + aviso_img + '<br><br>' + aviso_msg + aviso_btn + ' ' + aviso_test + '</div>'
    p += '<div class="' + yt_card_cls + '" ' + yt_card_click + '><h3>YouTube @mmrid07 <span style="color:' + yt_color + '">' + yt_mark + '</span></h3>' + yt_time_str + yt_img + '<br><br>' + yt_msg + yt_btn + ' ' + yt_test + '</div>'
    p += '<div id="testStatus" class="loading"></div>'
    p += '<script>function testSite(s){var d=document.getElementById("testStatus");d.style.display="block";d.innerHTML="Testing "+s+" with Selenium...";fetch(window.location.origin+"/test_cookies?site="+s+"&token=' + token + '",{method:"POST"}).then(function(r){return r.json()}).then(function(j){d.innerHTML="Done! Refreshing...";setTimeout(function(){location.reload()},2000)}).catch(function(e){d.innerHTML="Error: "+e.message})}</script>'
    p += '</body></html>'
    return p

if __name__ == '__main__':
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('127.0.0.1', 0))
    port = sock.getsockname()[1]
    sock.close()
    with open(os.path.expanduser('~/flask.port'), 'w') as f:
        f.write(str(port))
    app.run(host='127.0.0.1', port=port)