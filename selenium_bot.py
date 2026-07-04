import json
import os
import threading
import time
import subprocess

_driver = None
_starting = False
_driver_lock = threading.Lock()
_stop_event = threading.Event()
_ffmpeg_proc = None

DISPLAY_NUM = ":99"

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

def _start_xvfb():
    print("🚀 جاري تشغيل Xvfb...")
    subprocess.Popen(
        ["sudo", "Xvfb", DISPLAY_NUM, "-screen", "0", "1280x720x24"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    time.sleep(3)
    subprocess.run(["xhost", "+local:"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def _kill_all():
    print("🔄 جاري تنظيف العمليات القديمة وتهيئة البيئة...")
    subprocess.run(["pkill", "-9", "-f", "chromium"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["pkill", "-9", "-f", "ffmpeg"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["sudo", "pkill", "-9", "-f", "Xvfb"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["sudo", "rm", "-f", f"/tmp/.X{DISPLAY_NUM.replace(':', '')}-lock"])
    subprocess.run(["sudo", "rm", "-rf", "/tmp/.X11-unix"])
    subprocess.run(["sudo", "mkdir", "-p", "/tmp/.X11-unix"])
    subprocess.run(["sudo", "chown", "root:root", "/tmp/.X11-unix"])
    subprocess.run(["sudo", "chmod", "1777", "/tmp/.X11-unix"])

def _bot_worker(user_agent):
    global _driver, _ffmpeg_proc
    _kill_all()
    _start_xvfb()
    os.environ["DISPLAY"] = DISPLAY_NUM
    ffmpeg_cmd = [
        'ffmpeg', '-y',
        '-f', 'x11grab',
        '-video_size', '1280x720',
        '-i', DISPLAY_NUM,
        '-f', 'image2',
        '-update', '1',
        '-vcodec', 'mjpeg',
        '-q:v', '5',
        'udp://127.0.0.1:9999?pkt_size=60000'
    ]
    _ffmpeg_proc = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        driver = create_driver(user_agent)
        with _driver_lock:
            _driver = driver
        driver.get("https://aviso.bz")
        cookie_path = os.path.expanduser("~/aviso_cookies.json")
        if os.path.exists(cookie_path):
            load_cookies(driver, cookie_path)
            driver.get("https://aviso.bz")
            time.sleep(5)
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
