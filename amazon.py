import os
from pathlib import Path

import sys
import time

from sys import platform
from backports import configparser
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, WebDriverException
from twilio.rest import Client
from webdriver_manager.firefox import GeckoDriverManager
from twilio.base.exceptions import TwilioRestException
from selenium.webdriver.firefox.options import FirefoxProfile

global profile_path
global attempting_to_buy

'''Pretty sure bot works for the most part. However, the bot breaks when the out of stock
page shows up, so I tried to implement a fix around line 186. This all depends if the out
of stock URL is different from the amazon_page URL. If it is different, you will need to 
remove the comments on the if/else statements, put in the url in the if statement, and 
tab over the four lines under else:. I'm sure there's an easier way to go about this so don't 
hesitate to help'''

# 1. Amazon credentials
username = ''
password = ''

    
# 3. Main Config
amazon_page = ''  # The URL to use
interval = 4  # Refresh the page every X seconds (If your internet is slow and the page isn't fully loading, increase this)
auto_buy = True  # If false will sit on final place order screen, use for testing
# ----- You are done setting up the bot! -----


def time_sleep(x, driver):
    for i in range(x, -1, -1):
        sys.stdout.write('\r')
        sys.stdout.write('{:2d} seconds'.format(i))
        sys.stdout.flush()
        time.sleep(1)

    if not attempting_to_buy:
        driver.execute_script('window.localStorage.clear();')
        try:
            driver.refresh()
        except WebDriverException:
            print('Error while refreshing - internet down?')
        sys.stdout.write('\r')
        sys.stdout.write('Page refreshed\n')
        sys.stdout.flush()


def get_profile_path():
    global profile_path
    if platform == 'linux' or platform == 'linux2':
        profile_path = Path(os.getenv('HOME')) / '.mozilla' / 'firefox'
    elif platform == 'darwin':
        profile_path = Path(os.getenv('HOME')) / \
            'Library' / 'Application Support' / 'Firefox'
    elif platform == 'win32':
        profile_path = Path(os.getenv('APPDATA')) / 'Mozilla' / 'Firefox'
    if not profile_path.exists():
        raise FileNotFoundError("Mozilla profile doesn't exist and/or can't be located on this machine.")
    return profile_path


def get_default_profile(profile_path2):
    mozilla_profile_ini = profile_path2 / 'profiles.ini'
    profile = configparser.ConfigParser()
    profile.read(mozilla_profile_ini)
    return profile.get('Profile0', 'Path')


def prepare_sniper_profile(default_profile_path):
    profile = FirefoxProfile(default_profile_path.resolve())
    profile.set_preference('dom.webdriver.enabled', False)
    profile.set_preference('useAutomationExtension', False)
    profile.update_preferences()
    return profile


def create_driver():
    global profile_path
    profile_path = get_profile_path()
    default_profile = get_default_profile(profile_path)
    print(f'Launching Firefox using default profile: {default_profile}')
    profile = prepare_sniper_profile(profile_path / default_profile)
    driver = webdriver.Firefox(firefox_profile=profile, executable_path=GeckoDriverManager().install())
    return driver


def driver_wait(driver, find_type, selector, click=True):
    """Driver Wait Settings."""
    loop_id = 0
    while True:
        loop_id += 1
        if find_type == 'css':
            try:
                el = driver.find_element_by_css_selector(selector)
                if el and click:
                    el.click()
                break
            except NoSuchElementException:
                driver.implicitly_wait(0.2)
        elif find_type == 'name':
            try:
                el = driver.find_element_by_name(selector)
                if el and click:
                    el.click()
                break
            except NoSuchElementException:
                driver.implicitly_wait(0.2)


def login_attempt(driver):
    """Attempting to login Amazon Account."""
    driver.get('https://www.amazon.com/gp/sign-in.html')
    try:
        username_field = driver.find_element_by_css_selector('#ap_email')
        username_field.send_keys(username)
        driver_wait(driver, 'css', '#continue')
        password_field = driver.find_element_by_css_selector('#ap_password')
        password_field.send_keys(password)
        driver_wait(driver, 'css', '#signInSubmit')
        time.sleep(2)
    except NoSuchElementException:
        pass
    driver.get(amazon_page)


def run_loop(driver):
    global attempting_to_buy
    time.sleep(1)

    while True:
        
        """Single product page, keep checking and refreshing."""
        attempting_to_buy = True
        bought = attempt_purchase(driver)
        if bought:
            break
        attempting_to_buy = False

        time_sleep(interval, driver)


def attempt_purchase(driver, index=-1):
    global auto_buy
    

    print(f'Item available! Attempting to buy..')
    try:
        driver.find_element_by_id('buy-now-button')  # Cannot buy for some reason
    except NoSuchElementException:
        print('Buy now button did not exist, going back')
        return False

    print('Buy now button was found. Clicking it now.')
    driver_wait(driver, 'css', '#buy-now-button')  # Clicks buy now
    try:
        asking_to_login = driver.find_element_by_css_selector('#ap_password').is_displayed()
        if asking_to_login:
            print('Attempting to log in (Session must have expired)..')
            try:
                driver.find_element_by_css_selector('#ap_password').send_keys(password)
                driver_wait(driver, 'css', '#signInSubmit')
            except NoSuchElementException:
                print('Failed to login when prompted..')
                go_home()  # Back to search
                return False
    except NoSuchElementException:
        pass

    """I have seen two types of screens here, one that is a modal with a button to place order (I believe amazon
    calls this "Turbo Checkout"), another is an entire new page. This may need tweaking."""
    if auto_buy:
        # Wait for checkout to load - turbo checkout is an iframe we have to attach into
        driver_wait(driver, 'css', '#turbo-checkout-iframe', False)
        iframe = driver.find_element_by_css_selector('#turbo-checkout-iframe')
        driver.switch_to.frame(iframe)
        driver_wait(driver, 'css', '.a-color-price', False)  # Wait for inner iframe content to load
        
        #this might work idk. if statement that says if the url of the out of stock statement pops up, then go home.
        '''if driver.current_url == 'out of stock url here':
            go_home()
            return False'''
        #indent the four lines under else if you find out of stock url
        #else:
        driver_wait(driver, 'css', '#turbo-checkout-panel-container', False)  # Without this order doesnt go through for some reason, just blanks the page
        driver_wait(driver, 'css', '#turbo-checkout-pyo-button')  # Click place order button on modal
        notify_and_exit()
        return True

    else:
        print('Auto buy was not enabled, waiting on purchase screen..')
        try:
            client.messages.create(to=toNumber, from_=fromNumber, body=f'Item available! (auto_buy=False)! Link: {driver.current_url}')
        except (NameError, TwilioRestException):
            pass
        return True

def notify_and_exit():
    global auto_buy

    print(f'Order should be placed')
    for i in range(3):
        print('\a')
        time.sleep(1)
    time.sleep(1800)
    driver.quit()
    auto_buy = False  # Safety
    return True

def go_home():
    try:
        driver.get(amazon_page)
    except WebDriverException:
        print('Failed to load page - internet down?')

if __name__ == '__main__':
    driver = create_driver()
    login_attempt(driver)
    attempting_to_buy = False
    run_loop(driver)
