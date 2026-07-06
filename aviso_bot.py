import os
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium_bot import load_cookies, stop_bot


def login_aviso(driver):
    driver.get("https://aviso.bz")
    cookie_path = os.path.expanduser("~/aviso_cookies.json")
    if os.path.exists(cookie_path):
        load_cookies(driver, cookie_path)
        driver.get("https://aviso.bz/members")
        time.sleep(8)
        if "/login" in driver.current_url:
            os.remove(cookie_path)
            stop_bot()
            return False
        return True
    return False


def check_yt(driver):
    driver.get("https://www.youtube.com/feed/library")
    cookie_path = os.path.expanduser("~/youtube_cookies.json")
    if not os.path.exists(cookie_path):
        return False
    load_cookies(driver, cookie_path)
    driver.refresh()
    time.sleep(5)
    try:
        WebDriverWait(driver, 30).until(
            EC.visibility_of_any_elements_located(
                (By.CSS_SELECTOR, ".ytSpecButtonShapeNextHost.ytSpecButtonShapeNextOutline.ytSpecButtonShapeNextCallToAction.ytSpecButtonShapeNextSizeM.ytSpecButtonShapeNextIconLeading.ytSpecButtonShapeNextEnableBackdropFilterExperiment")
            )
        )
        os.remove(cookie_path)
        return False
    except:
        return True


def check_sub(driver):
    if check_yt(driver):
        driver.get("https://www.youtube.com/@mmrid07?hl=en")
        time.sleep(5)
        subb = WebDriverWait(driver, 30).until(
            EC.visibility_of_element_located((By.CLASS_NAME, "ytSpecButtonShapeNextButtonTextContent"))
        )
        if subb.text.lower() == "subscribed":
            return True
        else:
            subb.click()
    else:
        return False
