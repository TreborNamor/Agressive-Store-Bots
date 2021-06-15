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
from selenium.webdriver.firefox.options import Options

global profile_path

# ----- setting up the bot! -----

# 1. Amazon credentials
username = ''
password = ''

# 2. Main Config
url = 'https://www.amazon.com/PlayStation-5-Console/dp/B08FC5L3RG/ref=sr_1_6?dchild=1&keywords=ps5+console&qid=1623757970&sr=8-6'  # Enter your product page URL.
max_price = 800  # Enter your Max Price your willing to pay and include taxes.
webpage_refresh_timer = 4  # Default 4 seconds. If slow internet and the page isn't fully loading, increase this.
test_mode = True  # Set False for testing. If set to True, it will place order and checkout product.
headless_mode = False  # Set False for testing. If True, it will hide Firefox in background for faster checkout speed.

# 3. Twilio Information (Twilio is Optional - Skip this entire step if you don't want to use Twilio).
toNumber = 'Your_Phone_Number'
fromNumber = 'Twilio_Phone_Number'
accountSid = 'Twilio_SSID'
authToken = 'Twilio_AuthToken'
client = Client(accountSid, authToken)

# ----- You are done setting up the bot! -----


def time_sleep(x, driver):
    for i in range(x, -1, -1):
        sys.stdout.write('\r')
        sys.stdout.write('Monitoring Page. Refreshing in{:2d} seconds'.format(i))
        sys.stdout.flush()
        time.sleep(1)
    driver.execute_script('window.localStorage.clear();')

    if not attempting_to_buy:
        driver.execute_script('window.localStorage.clear();')
        try:
            driver.refresh()
        except WebDriverException:
            print('Error while refreshing - internet down?')
        sys.stdout.write('\r')
        sys.stdout.write('Monitoring Page. Refreshing in{:2d} seconds'.format(i))
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
    options = Options()
    options.headless = headless_mode
    global profile_path
    profile_path = get_profile_path()
    default_profile = get_default_profile(profile_path)
    print(f'Launching Firefox using default profile: {default_profile}')
    profile = prepare_sniper_profile(profile_path / default_profile)
    driver = webdriver.Firefox(firefox_profile=profile, options=options, executable_path=GeckoDriverManager().install())
    return driver


def driver_wait(driver, find_type, selector, click=True):
    """Driver Wait Settings."""
    loop_id = 0
    while True:
        loop_id += 1
        if find_type == 'css':
            try:
                element = driver.find_element_by_css_selector(selector)
                if element and click:
                    element.click()
                break
            except NoSuchElementException:
                driver.implicitly_wait(0.2)
        elif find_type == 'name':
            try:
                element = driver.find_element_by_name(selector)
                if element and click:
                    element.click()
                break
            except NoSuchElementException:
                driver.implicitly_wait(0.2)


def login_attempt(driver):
    """Attempting to login Amazon Account."""
    driver.get('https://www.amazon.com/gp/sign-in.html')

    print("\nWelcome To Amazon Bot! Join The Discord To find out When Amazon drops GPU's and Consoles!")
    print("Discord: https://discord.gg/qQDvwT6q3e")
    print("Donations keep the script updated!\n")
    print("Cashapp Donation: $TreborNamor")
    print("Bitcoin Donation: 16JRvDjqc1HrdCQu8NRVNoEjzvcgNtf6zW ")
    print("Dogecoin Donation: DSdN7qR1QR5VjvR1Ktwb7x4reg7ZeiSyhi \n")
    print("Bot deployed!\n")

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
    driver.get(url)


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

        time_sleep(webpage_refresh_timer, driver)


def format_price(price_text):
    price = price_text.text
    price = price.replace('$', '')
    price = price.replace(',', '')
    price = price.replace('\n', '.')
    price = float(price)
    return price


def attempt_purchase(driver, index=-1):
    global test_mode

    try:
        buy_box = format_price(driver.find_element_by_id('price_inside_buybox'))
        if buy_box <= max_price:
            driver.find_element_by_id('buy-now-button')  # Attempt to find buy now button.
            print(f'Item available! Attempting to buy..')
            driver_wait(driver, 'css', '#buy-now-button')
        else:
            return False
    except NoSuchElementException:
        return False

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
    if not test_mode:
        # Wait for checkout to load - turbo checkout is an iframe we have to attach into
        driver_wait(driver, 'css', '#turbo-checkout-iframe', False)
        iframe = driver.find_element_by_css_selector('#turbo-checkout-iframe')
        driver.switch_to.frame(iframe)
        driver_wait(driver, 'css', '.a-color-price', False)  # Wait for inner iframe content to load

        # this might work idk. if statement that says if the url of the out of stock statement pops up, then go home.
        '''if driver.current_url == 'out of stock url here':
            go_home()
            return False'''
        # indent the four lines under else if you find out of stock url
        # else:
        driver_wait(driver, 'css', '#turbo-checkout-panel-container', False)  # Without this order doesnt go through for some reason, just blanks the page
        time.sleep(.5)
        driver_wait(driver, 'css', '#turbo-checkout-pyo-button')  # Click place order button on modal
        notify_and_exit()
        return True

    else:
        print('Test Mode is enabled, waiting on purchase screen..')
        try:
            client.messages.create(to=toNumber, from_=fromNumber,
                                   body=f'Item available! (test_mode=False)! Link: {driver.current_url}')
        except (NameError, TwilioRestException):
            pass
        return True


def notify_and_exit():
    global test_mode

    print(f'Order should be placed')
    for i in range(3):
        print('\a')
        time.sleep(1)
    time.sleep(1800)
    driver.quit()
    test_mode = False  # Safety
    return True


def go_home():
    try:
        driver.get(url)
    except WebDriverException:
        print('Failed to load page - internet down?')


if __name__ == '__main__':
    driver = create_driver()
    login_attempt(driver)
    run_loop(driver)
