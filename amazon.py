import bs4
import sys
import time
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from twilio.rest import Client
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager
from twilio.base.exceptions import TwilioRestException

# Amazon credentials
username = 'your_username'
password = 'your_password'

# Twilio configuration
toNumber = 'your_phonenumber'
fromNumber = 'twilio_phonenumber'
accountSid = 'ssid'
authToken = 'authtoken'
client = Client(accountSid, authToken)


def timeSleep(x, driver):
    for i in range(x, -1, -1):
        sys.stdout.write('\r')
        sys.stdout.write('{:2d} seconds'.format(i))
        sys.stdout.flush()
        time.sleep(1)
    driver.refresh()
    sys.stdout.write('\r')
    sys.stdout.write('Page refreshed\n')
    sys.stdout.flush()


def createDriver():
    """Creating driver."""
    options = Options()
    options.headless = False  # Change To False if you want to see Firefox Browser Again.
    profile = webdriver.FirefoxProfile(
        r'C:\Users\Trebor\AppData\Roaming\Mozilla\Firefox\Profiles\kwftlp36.default-release')
    driver = webdriver.Firefox(profile, options=options, executable_path=GeckoDriverManager().install())
    return driver


def driverWait(driver, findType, selector):
    """Driver Wait Settings."""
    while True:
        if findType == 'css':
            try:
                driver.find_element_by_css_selector(selector).click();
                break
            except NoSuchElementException:
                driver.implicitly_wait(0.2)
        elif findType == 'name':
            try:
                driver.find_element_by_name(selector).click();
                break
            except NoSuchElementException:
                driver.implicitly_wait(0.2)


def loginAttempt(driver):
    """Attempting to login Amazon Account."""
    driver.get('https://www.amazon.com/gp/sign-in.html')
    try:
        usernameField = driver.find_element_by_css_selector('#ap_email')
        usernameField.send_keys(username)
        driverWait(driver, 'css', '#continue')
        passwordField = driver.find_element_by_css_selector('#ap_password')
        passwordField.send_keys(password)
        driverWait(driver, 'css', '#signInSubmit')
        time.sleep(2)
    except NoSuchElementException:
        pass
    driver.get(
        'https://www.amazon.com/stores/GeForce/RTX3080_GEFORCERTX30SERIES/page/6B204EA4-AAAC-4776-82B1-D7C3BD9DDC82')


def findingCards(driver):
    """Scanning all cards."""
    while True:
        time.sleep(1)
        html = driver.page_source
        soup = bs4.BeautifulSoup(html, 'html.parser')
        try:
            findAllCards = soup.find_all('span', {'class': 'style__text__2xIA2'})
            for card in findAllCards:
                if 'Add to Cart' in card.get_text():
                    print('Card Available!')
                    driverWait(driver, 'css', '.style__addToCart__9TqqV')
                    driver.get('https://www.amazon.com/gp/cart/view.html?ref_=nav_cart')
                    driverWait(driver, 'css', '.a-button-input')
                    try:
                        askingToLogin = driver.find_element_by_css_selector('#ap_password').is_displayed()
                        if askingToLogin:
                            driver.find_element_by_css_selector('#ap_password').send_keys(password)
                            driverWait(driver, 'css', '#signInSubmit')
                    except NoSuchElementException:
                        pass
                    driverWait(driver, 'css', '.a-button-input')  # Final Checkout Button!
                    print('Order Placed')
                    try:
                        client.messages.create(to=toNumber, from_=fromNumber, body='ORDER PLACED!')
                    except (NameError, TwilioRestException):
                        pass
                    for i in range(3):
                        print('\a')
                        time.sleep(1)
                    time.sleep(1800)
                    driver.quit()
                    return
        except (AttributeError, NoSuchElementException, TimeoutError):
            pass
        timeSleep(5, driver)


if __name__ == '__main__':
    driver = createDriver()
    loginAttempt(driver)
    findingCards(driver)
