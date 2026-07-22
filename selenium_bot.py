import json
import os
import threading
import time
from xvfb_manager import _start_xvfb, _kill_all, start_ffmpeg, DISPLAY_NUM

_driver = None
_starting = False
_driver_lock = threading.Lock()
_stop_event = threading.Event()
_ffmpeg_proc = None
_bot_thread = None

def create_driver(user_agent=None):
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    options = Options()
    options.binary_location = "/usr/bin/chromium"

    prefs = {"profile.default_content_setting_values.notifications": 2}
    options.add_experimental_option("prefs", prefs)
    options.add_argument("--lang=en")
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    options.add_argument('--ignore-certificate-errors-spki-list')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--ignore-ssl-errors')
    options.add_experimental_option("detach", True)
    options.add_experimental_option("useAutomationExtension", False)
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_argument("disable-blink-features")
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-gpu')
    options.add_argument("--log-level=3")
    options.add_experimental_option('w3c', True)
    options.add_argument("--disable-web-security")
    options.add_argument("--allow-running-insecure-content")
    options.add_argument('--disable-logging')
    options.add_argument("--mute-audio")
    options.add_argument("--no-sandbox")
    options.add_argument('--window-size=1280,720')
    if user_agent:
        options.add_argument(f"--user-agent={user_agent}")

    service = Service(executable_path="/usr/bin/chromedriver")
    service.env = {"DISPLAY": DISPLAY_NUM}
    return webdriver.Chrome(service=service, options=options)

def load_cookies(driver, filepath):
    with open(filepath) as f:
        cookies = json.load(f)
    for cookie in cookies:
        try:
            driver.add_cookie(cookie)
        except Exception as e:
            print(f"Cookie add failed: {cookie.get('name')}: {e}")





def _bot_worker(user_agent):
    from aviso_bot import login_aviso, check_sub
    global _driver, _ffmpeg_proc, _bot_thread, _starting
    try:
        _kill_all()
        _start_xvfb()
        os.environ["DISPLAY"] = DISPLAY_NUM
        _ffmpeg_proc = start_ffmpeg()
        driver = create_driver(user_agent)
        with _driver_lock:
            _driver = driver
        if login_aviso(driver):
            cheker = check_sub(driver)
            if cheker:
                pass
            else:
                pass
        else:
            return
        driver.save_screenshot(os.path.expanduser("~/aviso_screenshot.png"))
        _stop_event.wait()
    except Exception as e:
        print(f"⚠️ حدث خطأ أثناء تشغيل البوت: {e}")
    finally:
        print("🛑 جاري إغلاق البوت وتنظيف الذاكرة...")
        if _ffmpeg_proc:
            _ffmpeg_proc.kill()
            _ffmpeg_proc = None
        try:
            if _driver:
                _driver.quit()
        except:
            pass
        _kill_all()
        with _driver_lock:
            _driver = None
            _starting = False
        _bot_thread = None

def start_bot(user_agent=None):
    global _bot_thread
    if not user_agent:
        ua_path = os.path.expanduser("~/user_agent.json")
        if os.path.exists(ua_path):
            with open(ua_path) as f:
                user_agent = json.load(f).get("user_agent", "")
    with _driver_lock:
        if _driver is not None:
            return False
        _starting = True
        _stop_event.clear()
    thread = threading.Thread(target=_bot_worker, args=(user_agent,), daemon=True)
    thread.start()
    _bot_thread = thread
    return True

def stop_bot():
    global _bot_thread
    _stop_event.set()
    if _bot_thread is not None:
        _bot_thread.join(timeout=10)
        _bot_thread = None

def is_running():
    with _driver_lock:
        return _starting or _driver is not None
