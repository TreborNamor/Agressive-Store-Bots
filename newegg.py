import bs4
import sys
import time
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, ElementNotInteractableException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.firefox.options import Options
import random

# Newegg credentials
username = 'your_username'
password = 'your_password'
cvv = '123'

# Twilio configuration
toNumber = 'your_phonenumber'
fromNumber = 'twilio_phonenumber'
accountSid = 'ssid'
authToken = 'authtoken'
client = Client(accountSid, authToken)

# insert your URL here. Default RTX 3080
url = 'https://www.newegg.com/p/pl?d=rtx+3080&N=100007709%20601357282%204841&isdeptsrh=1' 
# Please do not use URL of a Specific Product like the example URL below. 
# https://www.newegg.com/evga-geforce-rtx-3080-10g-p5-3895-kr/p/N82E16814487519?Description=rtx%203080&cm_re=rtx_3080-_-14-487-519-_-Product
# If you are only interested in a specific graphics card. Use a URL link like this instead. 
# You'll see how I used newegg filters on the website to only show a specific card in the URL below.
# https://www.newegg.com/p/pl?d=rtx+3080&N=100007709%20601357282%2050001402&isdeptsrh=1&LeftPriceRange=860+880


def time_sleep(x, driver):
    for i in range(x, -1, -1):
        sys.stdout.write('\r')
        sys.stdout.write('{:2d} seconds'.format(i))
        sys.stdout.flush()
        time.sleep(1)
    driver.execute_script('window.localStorage.clear();')
    driver.refresh()
    sys.stdout.write('\r')
    sys.stdout.write('Page refreshed\n')
    sys.stdout.flush()


def create_driver():
    """Creating driver."""
    options = Options()
    options.headless = False  # Change To False if you want to see Firefox Browser Again.
    profile = webdriver.FirefoxProfile(r'C:\Users\Trebor\AppData\Roaming\Mozilla\Firefox\Profiles\kwftlp36.default-release')
    driver = webdriver.Firefox(profile, options=options, executable_path=GeckoDriverManager().install())
    return driver


def driver_wait(driver, find_type, selector):
    """Driver Wait Settings."""
    while True:
        if find_type == 'css':
            try:
                driver.find_element_by_css_selector(selector).click()
                break
            except NoSuchElementException:
                driver.implicitly_wait(0.5)
        elif find_type == 'name':
            try:
                driver.find_element_by_name(selector).click()
                break
            except NoSuchElementException:
                driver.implicitly_wait(0.5)


def finding_cards(driver):
    """Scanning all cards."""
    print("That piece of red text above is not an error. Not sure why they would use that color.")
    print("If you keep seeing page refreshed, the bot is working.")
    print("Goodluck!")
    # time.sleep(1)
    driver.get(url)
    while True:
        html = driver.page_source
        soup = bs4.BeautifulSoup(html, 'html.parser')
        wait = WebDriverWait(driver, 5)
        try:
            find_all_cards = soup.find('button', {'class': 'btn btn-primary btn-mini'})
            if find_all_cards:
                print(f'Button Found!: {find_all_cards.get_text()}')
                time.sleep(1)

                # Clicking Add to Cart.
                driver.find_element_by_xpath("//*[@class='btn btn-primary btn-mini']").click()
                # time.sleep(2)

                # Going To Cart.
                driver.get('https://secure.newegg.com/shop/cart')

                # Checking if item already sold out after clicking to cart.
                try:
                    out_of_stock = driver.find_element_by_xpath("//*[@class='btn btn-secondary']").is_enabled()
                    if out_of_stock:
                        driver.find_element_by_xpath("//*[@class='btn btn-secondary']").click()
                        print("Item Is Not In Cart Anymore. Retrying..")
                        time_sleep(1, driver)
                        driver.get(url)
                        time_sleep(2, driver)
                        finding_cards(driver)
                        return
                    if not out_of_stock:
                        pass
                except (TimeoutException, NoSuchElementException, ElementNotInteractableException):
                    pass

                try:
                    available = driver.find_element_by_xpath("//*[@class='btn btn-primary btn-wide']").is_enabled()
                    if available:
                        driver.find_element_by_xpath("//*[@class='btn btn-primary btn-wide']").click()
                        print("Clicked Checkout Button in Cart.")
                    if not available:
                        print("Item Is Not In Cart Anymore. Retrying..")
                        time_sleep(1, driver)
                        driver.get(url)
                        time_sleep(2, driver)
                        finding_cards(driver)
                        return
                except (TimeoutException, NoSuchElementException):
                    print("Item Is Not In Cart Anymore. Retrying..")
                    driver.get(url)
                    time_sleep(3, driver)
                    finding_cards(driver)
                    return

                # Logging Into Account.
                try:
                    print("Attempting Sign-In.")
                    wait.until(ec.visibility_of_element_located((By.ID, "labeled-input-password")))
                    password_field = driver.find_element_by_id("labeled-input-password")
                    time.sleep(1)
                    password_field.send_keys(password)
                    password_field.send_keys(Keys.ENTER)
                except (NoSuchElementException, TimeoutException):
                    print("Could Not Login To Account With Password.")

                # Submit CVV Code(Must type CVV number.
                try:
                    print("Trying Credit Card CVV Number.")
                    wait.until(ec.visibility_of_element_located(
                        (By.XPATH, "//input[@class='form-text mask-cvv-4'][@type='text']")))
                    security_code = driver.find_element_by_xpath("//input[@class='form-text mask-cvv-4'][@type='text']")
                    time.sleep(.5)
                    security_code.send_keys(Keys.BACK_SPACE + Keys.BACK_SPACE + Keys.BACK_SPACE + Keys.BACK_SPACE + cvv)
                except (AttributeError, NoSuchElementException, TimeoutException, ElementNotInteractableException):
                    print("Could Not Type CVV.")

                # Final Checkout
                try:
                    wait.until(ec.visibility_of_element_located((By.XPATH, "//*[@class='btn btn-primary btn-wide']")))
                    driver.find_element_by_xpath("//*[@class='btn btn-primary btn-wide']").click()
                except (NoSuchElementException, TimeoutException, ElementNotInteractableException):
                    print("Could Not proceed with Checkout.")

                # Completed Checkout.
                print('Order Placed!')
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

        except NoSuchElementException:
            pass
        time_sleep(10, driver) 


if __name__ == '__main__':
    driver = create_driver()
    finding_cards(driver)
