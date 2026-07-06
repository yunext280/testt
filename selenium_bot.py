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

def create_driver(user_agent=None):
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    options = Options()
    options.binary_location = "/usr/bin/chromium"
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1280,720")
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
    global _driver, _ffmpeg_proc
    _kill_all()
    _start_xvfb()
    os.environ["DISPLAY"] = DISPLAY_NUM
    _ffmpeg_proc = start_ffmpeg()
    try:
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

def start_bot(user_agent=None):
    with _driver_lock:
        if _driver is not None:
            return False
        _starting = True
        _stop_event.clear()
    thread = threading.Thread(target=_bot_worker, args=(user_agent,), daemon=True)
    thread.start()
    return True

def stop_bot():
    _stop_event.set()
    return True

def is_running():
    with _driver_lock:
        return _starting or _driver is not None
