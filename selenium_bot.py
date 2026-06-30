import json, os, threading, time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

_driver = None
_driver_lock = threading.Lock()
_stop_event = threading.Event()

def create_driver(user_agent=None):
    options = Options()
    options.binary_location = "/usr/bin/chromium"
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    if user_agent:
        options.add_argument(f"--user-agent={user_agent}")
    service = Service(executable_path="/usr/bin/chromedriver")
    return webdriver.Chrome(service=service, options=options)

def load_cookies(driver, filepath):
    with open(filepath) as f:
        cookies = json.load(f)
    for cookie in cookies:
        try:
            driver.add_cookie(cookie)
        except:
            pass

def _bot_worker(user_agent):
    global _driver
    driver = create_driver(user_agent)
    with _driver_lock:
        _driver = driver
    try:
        driver.get("https://aviso.bz")
        cookie_path = os.path.expanduser("~/aviso_cookies.json")
        if os.path.exists(cookie_path):
            load_cookies(driver, cookie_path)
            driver.get("https://aviso.bz")
            time.sleep(5)
        driver.save_screenshot(os.path.expanduser("~/aviso_screenshot.png"))
        _stop_event.wait()
    finally:
        try:
            driver.quit()
        except:
            pass
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
