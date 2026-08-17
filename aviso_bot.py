import os, re
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium_bot import load_cookies, should_stop, stop_bot, close_tap, interruptible_sleep,complete_page


def login_aviso(driver):
    driver.get("https://aviso.bz")
    if should_stop():
        return False
    cookie_path = os.path.expanduser("~/aviso_cookies.json")
    if os.path.exists(cookie_path):
        load_cookies(driver, cookie_path)
        driver.get("https://aviso.bz/members")
        for _ in range(16):
            if should_stop():
                return False
            time.sleep(0.5)
        if "/login" in driver.current_url:
            os.remove(cookie_path)
            sel_path = os.path.expanduser("~/sel_bot.json")
            if os.path.exists(sel_path):
                os.remove(sel_path)
            stop_bot()
            return False
        return True
    return False


def scrol_Surfing(driver:webdriver,second:int,ads:object) -> None:
    if should_stop():
        return
    try:
        close_tap(driver)
        driver.switch_to.window(driver.window_handles[0])
        driver.execute_script("arguments[0].scrollIntoView(true);",ads)
        ser = ads.get_attribute('id')
        serf_id=ser.replace('serf-link-','serf-id-')
        sek = WebDriverWait(driver, second).until(EC.invisibility_of_element((By.XPATH,f'//*[@id="{serf_id}"]/div/b[2]'))).get_attribute("outerHTML")
        sek = int(re.findall(r'\d+', sek)[0])
        serf= ser.replace('serf-link-','start-serf-')
        try:
            WebDriverWait(driver, second).until(EC.element_to_be_clickable((By.XPATH,f'//*[@id="{serf}"]/a'))).click()
            interruptible_sleep(second//6)
            if len(driver.window_handles)>1:
                driver.switch_to.window(driver.window_handles[1])
                interruptible_sleep(second//6)
                interruptible_sleep(sek+5)
                driver.switch_to.window(driver.window_handles[0])
                confer=ser.replace('serf-link-','serf_btn_confirm_')
                interruptible_sleep(second//10)
                WebDriverWait(driver, second).until(EC.element_to_be_clickable((By.ID,confer))).click()
                interruptible_sleep(second//10)
                close_tap(driver)
                interruptible_sleep(second//10)
        except:
            WebDriverWait(driver, second).until(EC.visibility_of_element_located((By.CSS_SELECTOR,f'.h-captcha')))
    except:
        close_tap(driver)        

def Surfing(driver:webdriver,second:int) -> list:
    try:
        driver.get("https://aviso.bz/tasks-surf")
        if complete_page(driver):
            secondd = second //10
        Surfing_ads = WebDriverWait(driver,second).until(EC.visibility_of_any_elements_located((By.CLASS_NAME,'work-serf')))
        return Surfing_ads
    except:
        return []

def av_ytub_ref(driver:webdriver,second:int,tube:object) -> dict:
    driver.switch_to.window(driver.window_handles[0])
    driver.execute_script("arguments[0].scrollIntoView(true);",tube)
    tub_id = tube.get_attribute('id')
    try:
        if 'ads-link-' in tub_id:
            sek_id = tub_id.replace('ads-link-','ads_id_')
            sek = WebDriverWait(driver, second).until(EC.invisibility_of_element((By.XPATH,f'//*[@id="{sek_id}"]/span/b[2]'))).get_attribute("outerHTML")
            sek  = int(re.findall(r'\d+', sek)[0])
            tub=tub_id.replace('ads-link-','link_ads_start_')
            WebDriverWait(driver,second).until(EC.element_to_be_clickable((By.ID,tub))).click()
            data = yt_url(driver,second,sek,tub_id)
            if data:
                return data
        return {"data":True}
    except:
        try:
            close_tap(driver)
            interruptible_sleep(3)
            driver.switch_to.window(driver.window_handles[0])
            qq =WebDriverWait(driver,second).until(EC.visibility_of_element_located((By.CSS_SELECTOR,f'#{tub_id} > tbody > tr > td:nth-child(3) > div > a')))
            qq.click()
            interruptible_sleep(5)
            return {"data":'rmove true'}
        except:
            return {"data":'break'}

def yt_url(driver,second,sek,tub_id):
    if len(driver.window_handles)>1:
        driver.switch_to.window(driver.window_handles[1])
        interruptible_sleep(second//10)
        if "youtube.com/watch?v" in driver.current_url:
            interruptible_sleep(second//5)
            interruptible_sleep(sek+5)
            driver.switch_to.window(driver.window_handles[0])
            ttit = driver.title.strip()
            if ttit == 'Подтвердить просмотр'.strip():
                btn_co_yt(driver,second,tub_id)
                close_tap(driver)  
            else:
                driver.switch_to.window(driver.window_handles[1])
                seek = re.findall(r'\d+', ttit)
                if len(seek) != 0:
                    seekk = int(seek[0])
                    interruptible_sleep(seekk)
                interruptible_sleep(second//5)
                btn_co_yt(driver,second,tub_id)       
        else:
            data = next_step(driver,second,sek,tub_id)
            interruptible_sleep(second//10)     
            return data    

def next_step(driver:webdriver,second:int,sek:int,tub_id) -> dict:
    """
    {"sek":sek,"tub_id":tub_id}
    """
    if complete_page(driver):
        secondd = second //10
    try:
        try:
            WebDriverWait(driver,secondd).until(EC.element_to_be_clickable((By.CLASS_NAME,"btn__notice"))).click()
        except:
            WebDriverWait(driver,secondd).until(EC.element_to_be_clickable((By.ID,"youtube_views-channel-link"))).click()
    except:
        WebDriverWait(driver, secondd).until(EC.visibility_of_element_located((By.CSS_SELECTOR,f'.h-captcha')))

        return {"sek":sek,"tub_id":tub_id} # <<<<<<<<<<<<<
    
    interruptible_sleep(second//5)
    interruptible_sleep(sek+5)
    driver.switch_to.window(driver.window_handles[0])
    ttit = driver.title.strip()
    if ttit == 'Подтвердить просмотр'.strip():
        btn_co_yt(driver,second,tub_id)
        close_tap(driver)  
    else:
        driver.switch_to.window(driver.window_handles[1])
        seek = re.findall(r'\d+', ttit)
        if len(seek) > 0:
            seekk = int(seek[0])
            interruptible_sleep(seekk)
        interruptible_sleep(second//5)
        btn_co_yt(driver,second,tub_id)
        close_tap(driver)  
    return {"data":True}

def btn_co_yt(driver:webdriver,second:int,tub_id:str) -> None:
    try:
        driver.switch_to.window(driver.window_handles[0])
        interruptible_sleep(second//5)
        comf = tub_id.replace('ads-link-','ads_btn_confirm_')
        WebDriverWait(driver,second).until(EC.element_to_be_clickable((By.ID,comf))).click()
        interruptible_sleep(second//10)
        close_tap(driver)    
    except:
        pass

def av_ytub(driver:webdriver,second:int) -> list:
    try:
        driver.get("https://aviso.bz/tasks-youtube")
        all_tube = WebDriverWait(driver,second).until(EC.visibility_of_any_elements_located((By.CLASS_NAME,'work-serf')))
        tes = len(all_tube)//2
        if 'ads-link' in all_tube[tes].get_attribute('id'):
            return all_tube
        return []
    except:
        return []


def chek_captcha(driver,second) -> bool:
    try:
        WebDriverWait(driver, second).until(EC.visibility_of_element_located((By.CSS_SELECTOR,f'.h-captcha')))
        return True
    except:
        return False



# def check_yt(driver):
#     cookie_path = os.path.expanduser("~/youtube_cookies.json")
#     if not os.path.exists(cookie_path):
#         return False
#     driver.get("https://www.youtube.com/feed/library")
#     load_cookies(driver, cookie_path)
#     driver.refresh()
#     time.sleep(5)
#     try:
#         WebDriverWait(driver, 30).until(
#             EC.visibility_of_any_elements_located(
#                 (By.CSS_SELECTOR, ".ytSpecButtonShapeNextHost.ytSpecButtonShapeNextOutline.ytSpecButtonShapeNextCallToAction.ytSpecButtonShapeNextSizeM.ytSpecButtonShapeNextIconLeading.ytSpecButtonShapeNextEnableBackdropFilterExperiment")
#             )
#         )
#         os.remove(cookie_path)
#         return False
#     except:
#         return True


# def check_sub(driver):
#     if check_yt(driver):
#         driver.get("https://www.youtube.com/@only_with_bot?hl=en")
#         time.sleep(5)
#         subb = WebDriverWait(driver, 30).until(
#             EC.visibility_of_element_located((By.CLASS_NAME, "ytSpecButtonShapeNextButtonTextContent"))
#         )
#         if subb.text.lower() == "subscribed":
#             return True
#         else:
#             subb.click()
#             return True
#     else:
#         return False
