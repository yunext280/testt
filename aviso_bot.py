import os
import time
from selenium_bot import load_cookies, stop_bot


def login_aviso(driver):
    driver.get("https://aviso.bz")
    cookie_path = os.path.expanduser("~/aviso_cookies.json")
    if os.path.exists(cookie_path):
        load_cookies(driver, cookie_path)
        driver.get("https://aviso.bz/members")
        time.sleep(5)
        if driver.current_url == 'https://aviso.bz/login':
            os.remove(cookie_path)
            stop_bot()
            return False
        return True
    return False
