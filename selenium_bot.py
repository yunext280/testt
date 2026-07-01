import json, os, threading, time, subprocess

_driver = None
_driver_lock = threading.Lock()
_stop_event = threading.Event()
_ffmpeg_proc = None

def create_driver(user_agent=None):
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    options = Options()
    options.binary_location = "/usr/bin/chromium"
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=405,720")
    if user_agent:
        options.add_argument(f"--user-agent={user_agent}")
    service = Service(executable_path="/usr/bin/chromedriver")
    service.env = {"DISPLAY": ":1"}
    return webdriver.Chrome(service=service, options=options)

def load_cookies(driver, filepath):
    with open(filepath) as f:
        cookies = json.load(f)
    for cookie in cookies:
        try:
            driver.add_cookie(cookie)
        except:
            pass

def _start_xvfb():
    subprocess.run("Xvfb :99 -screen 0 405x720x24 &", shell=True)
    time.sleep(1)

def _kill_all():
    subprocess.run("pkill -9 -f chromium; pkill -9 -f ffmpeg; pkill -9 -f Xvfb; rm -rf /tmp/.X*-lock /tmp/.X11-unix/X*", shell=True)

def _bot_worker(user_agent):
    global _driver, _ffmpeg_proc
    _kill_all()
    _start_xvfb()
    os.environ["DISPLAY"] = ":99"
    driver = create_driver(user_agent)
    with _driver_lock:
        _driver = driver
    try:
        driver.get("https://aviso.bz")
        cookie_path = os.path.expanduser("~/aviso_cookies.json")
        if os.path.exists(cookie_path):
            load_cookies(driver, cookie_path)
            driver.get("https://aviso.bz")
            time.sleep(3)
        driver.save_screenshot(os.path.expanduser("~/aviso_screenshot.png"))
        ffmpeg_cmd = [
            'ffmpeg', '-y',
            '-f', 'x11grab',
            '-video_size', '405x720',
            '-i', ':99',
            '-f', 'image2',
            '-update', '1',
            '-vcodec', 'mjpeg',
            '-q:v', '5',
            'udp://127.0.0.1:9999?pkt_size=60000'
        ]
        _ffmpeg_proc = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        _stop_event.wait()
    except:
        pass
    finally:
        if _ffmpeg_proc:
            _ffmpeg_proc.kill()
            _ffmpeg_proc = None
        try:
            driver.quit()
        except:
            pass
        _kill_all()
        with _driver_lock:
            _driver = None

def start_bot(user_agent=None):
    with _driver_lock:
        if _driver is not None:
            return False
        _stop_event.clear()
    thread = threading.Thread(target=_bot_worker, args=(user_agent,), daemon=True)
    thread.start()
    return True

def stop_bot():
    _stop_event.set()
    return True

def is_running():
    with _driver_lock:
        return _driver is not None
