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

# ---------------------------------------------Please Read--------------------------------------------------------------

# Updated: 4/19/2021

# Welcome to the Amazon script!
# Let's go over the checklist for the script to run properly.
#   1. Amazon login (Have your preferred payment method and shipping address set as defaults in amazon!)
#   2. Twilio Account (Optional, but free)
#   3. Config/Restrictions (Settings like URL, speed, price, etc.)

# This Script only accepts Product URL's or pages that look like this. I hope you see the difference between page examples.

# Example 1 - Nvidia RTX 3080:
# https://www.amazon.com/EVGA-GeForce-Technology-Backplate-24G-P5-3987-KR/dp/B08J5F3G18/
# Example 2 - Ryzen 5600x:
# https://www.amazon.com/AMD-Ryzen-5600X-12-Thread-Processor/dp/B08166SLDF
# Example 3 - Nvidia 30 Series Page:
# https://www.amazon.com/stores/GeForce/RTX3080_GEFORCERTX30SERIES/page/6B204EA4-AAAC-4776-82B1-D7C3BD9DDC82

# This Script does NOT accept Product URL's that look like this (Page search):
# https://www.amazon.com/s?k=rtx+3080&i=electronics&ref=nb_sb_noss_2

# Highly Recommend To set up Twilio Account to receive text messages. So if bot doesn't work you'll at least get a phone
# text message with the url link. You can click the link and try manually purchasing on your phone.

# Twilio is free. Get it Here:
# https://www.twilio.com/referral/BgLBXx

# -----------------------------------------------Steps To Complete------------------------------------------------------

# Fill out the amazon credentials below so the bot can login
# Setup twilio account and copy the api keys
# Setup the main configs. Step #2.5 is for product listing pages like the Nvidia page linked by default.
# If you want to test purchasing an item, set auto_buy to False!


# 1. Amazon credentials
username = 'your_username'
password = 'your_password'

# 2. Twilio Config
toNumber = 'your_phonenumber'
fromNumber = 'twilio_phonenumber'
accountSid = 'ssid'
authToken = 'authtoken'
client = Client(accountSid, authToken)

# (2.5) Special Config (For product listing page like at: https://www.amazon.com/stores/GeForce/RTX3080_GEFORCERTX30SERIES/page/6B204EA4-AAAC-4776-82B1-D7C3BD9DDC82)
# product_list_page MUST be set to True in the main config (Step 3) for these to take affect!
blacklisted = [0]  # Some listings should be ignored like gaming pc is first one. Index from 0-13 (Currently 13 listings on store) Ex: [0, 3]
item_must_include = ['3080']  # Strings the item title must include (Must have ALL of these) Use commas - Example with multiple: ['3080', 'gpu'] (Not case sensitive)
blacklisted_phrases = ['gaming pc']  # If the item has any of these phrases in its title it will be ignored (Not case sensitive)

# 3. Main Config
product_list_page = True  # Set to false if you have a single listing/item rather than a product/store page (Settings above)
amazon_page = 'https://www.amazon.com/stores/GeForce/RTX3080_GEFORCERTX30SERIES/page/6B204EA4-AAAC-4776-82B1-D7C3BD9DDC82'  # The URL to use
interval = 2  # Refresh the page every X seconds (If your internet is slow and the page isn't fully loading, increase this)
min_price = 499.0
max_price = 961.0
auto_buy = False  # If false will sit on final place order screen, use for testing
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
        if loop_id > 300:  # 60 sec
            print(f'Wait failed for selector "{selector}"!')
            break
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
        if product_list_page:
            """Scanning all cards."""
            try:
                find_all_cards = driver.find_elements_by_css_selector('.style__overlay__2qYgu.ProductGridItem__overlay__1ncmn')
                if len(find_all_cards) <= 0 and not attempting_to_buy:
                    print('Failed to find valid listings on products page, returning to set URL.')
                    go_home()
                    continue

                index = 0
                for card in find_all_cards:
                    status = ''
                    try:
                        status = card.parent.find_element_by_css_selector('.Availability__primaryMessage__1bDnl').text
                    except Exception:
                        print('Failed to find status text!')
                        index += 1
                        continue

                    if 'Currently unavailable' not in status and index not in blacklisted:
                        # Open listing
                        print('Opening item listing..')
                        card.click()
                        attempting_to_buy = True
                        bought = attempt_purchase(driver, index)
                        if bought:
                            break
                        attempting_to_buy = False
                    index += 1
            except (AttributeError, NoSuchElementException, TimeoutError) as e:
                print('Exception while scanning: ' + e)
                pass
        else:
            """Single product page, keep checking and refreshing."""
            attempting_to_buy = True
            bought = attempt_purchase(driver)
            if bought:
                break
            attempting_to_buy = False

        time_sleep(interval, driver)


def attempt_purchase(driver, index=-1):
    global auto_buy
    driver_wait(driver, 'css', '#priceblock_ourprice', False)  # Ensures page loads & get price

    try:
        price = driver.find_element_by_id('priceblock_ourprice')
        price = float(price.text.replace('$', ''))
        title = driver.find_element_by_id('productTitle').text
    except Exception as e:
        print('Failed to get price: ')
        print(e)
        go_home()
        return False

    # Title check
    if not check_name(title):
        print('Title did not pass requirements!')
        blacklisted.append(index)
        go_home()
        return False

    if min_price <= price <= max_price:
        print(f'Item available! (${str(price)}) "{title}" Attempting to buy..')
        try:
            driver.find_element_by_id('buy-now-button')  # Cannot buy for some reason
        except NoSuchElementException:
            print('Buy now button did not exist, going back')
            go_home()
            return False

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
            # Final price check on buying screen... to be sure
            price = -1.0
            try:
                price = driver.find_element_by_css_selector('.a-color-price')
                price = float(price.text.replace('$', ''))
            except Exception as e:
                print('Failed to get grand total price:')
                print(e)
                go_home()
                return False

            if min_price <= price <= max_price:
                driver_wait(driver, 'css', '#turbo-checkout-panel-container', False)  # Without this order doesnt go through for some reason, just blanks the page
                driver_wait(driver, 'css', '#turbo-checkout-pyo-button')  # Click place order button on modal
                notify_and_exit(title, price)
                return True
            else:
                print(f'Final price did not pass! (${str(price)})')
                go_home()
                return False
        else:
            print('Auto buy was not enabled, waiting on purchase screen..')
            try:
                client.messages.create(to=toNumber, from_=fromNumber, body=f'Item available! (auto_buy=False): "{title}" Price: ${str(price)}! Link: {driver.current_url}')
            except (NameError, TwilioRestException):
                pass
            return True
    else:
        blacklisted.append(index)
        print('Price did not pass ($' + str(price) + ')!')
        go_home()
        return False


def go_home():
    try:
        driver.get(amazon_page)
    except WebDriverException:
        print('Failed to load page - internet down?')


def check_name(title):
    passed = True
    for part in blacklisted_phrases:
        if part.lower() in title.lower():
            passed = False

    for part in item_must_include:
        if part.lower() not in title:
            passed = False

    return passed


def notify_and_exit(title, price):
    global auto_buy

    print(f'Order Placed for {title} Total: ${str(price)}! Notifying and exiting..')
    try:
        client.messages.create(to=toNumber, from_=fromNumber, body=f'Order Placed for "{title}" Total: ${str(price)}!')
    except (NameError, TwilioRestException):
        pass
    for i in range(3):
        print('\a')
        time.sleep(1)
    time.sleep(1800)
    driver.quit()
    auto_buy = False  # Safety
    return True


if __name__ == '__main__':
    driver = create_driver()
    login_attempt(driver)
    attempting_to_buy = False
    run_loop(driver)
