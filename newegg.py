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
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager

# Product Page
url = 'https://www.newegg.com/amd-ryzen-9-5900x/p/N82E16819113664'

# Price Limit
price_limit = 600

# Newegg credentials
username = 'your-email'
password = 'your-password'
cvv = 'your-CVV-number on credit card'

# Twilio configuration
toNumber = 'your_phonenumber'
fromNumber = 'twilio_phonenumber'
accountSid = 'ssid'
authToken = 'authtoken'
client = Client(accountSid, authToken)


def time_sleep(x, driver):
    for i in range(x, -1, -1):
        sys.stdout.write('\r')
        sys.stdout.write('{:2d} seconds'.format(i))
        sys.stdout.flush()
        time.sleep(1)
    driver.execute_script('window.localStorage.clear();')
    driver.refresh()


def create_driver():
    """Creating driver."""
    options = Options()
    options.headless = False  # Change To False if you want to see Firefox Browser Again.
    profile = webdriver.FirefoxProfile(
        r'C:\Users\Trebor\AppData\Roaming\Mozilla\Firefox\Profiles\t6inpqro.Robert-1613116705360')
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
                driver.implicitly_wait(1)
        elif find_type == 'name':
            try:
                driver.find_element_by_name(selector).click()
                break
            except NoSuchElementException:
                driver.implicitly_wait(1)
        elif find_type == 'xpath':
            try:
                driver.find_element_by_xpath(f"//*[@class='{selector}']").click()
                break
            except NoSuchElementException:
                driver.implicitly_wait(1)


def extract_page():
    html = driver.page_source
    soup = bs4.BeautifulSoup(html, 'html.parser')
    return soup


def single_search_item(soup):
    try:
        true = soup.find('button', {'class': 'btn btn-primary btn-wide'})
        if true:
            return True
    except (TimeoutException, NoSuchElementException, ElementNotInteractableException):
        return False


def search_multiple_items(soup):
    try:
        true = soup.find('button', {'class': 'btn btn-primary btn-mini'})
        if true:
            return True
    except (TimeoutException, NoSuchElementException, ElementNotInteractableException):
        return False


def check_price(soup):
    try:
        price = driver.find_element_by_xpath("//*[@class='price-current']")
        showPrice = float(price.text[1:])
        if showPrice <= price_limit:
            print(f'price is under: {price_limit}')
            return True
        else:
            return False
    except NoSuchElementException:
        print("Could not find price.")


def finding_cards(driver):
    """Scanning all cards."""

    driver.get(url)

    while True:
        wait = WebDriverWait(driver, 5)
        soup = extract_page()

        # Searching For Add To Cart Button.
        if single_search_item(soup=soup):
            if check_price(soup):
                driver_wait(driver, 'xpath', 'btn btn-primary btn-wide')
            else:
                time.sleep(2)
                finding_cards(driver)
            break
        elif search_multiple_items(soup=soup):
            try:
                driver_wait(driver, 'xpath', 'btn btn-primary btn-mini')
                break
            except (TimeoutException, NoSuchElementException, ElementNotInteractableException):
                time_sleep(5,driver)
                finding_cards(driver)
        else:
            time_sleep(6, driver)

    # Going To Cart.
    driver.get('https://secure.newegg.com/shop/cart')

    # Checking if item is still in cart.
    try:
        out_of_stock = driver.find_element_by_xpath("//*[@class='btn btn-secondary']").is_enabled()
        if out_of_stock:
            driver_wait(driver, 'xpath', 'btn btn-secondary')
            print("Item Is Not In Cart Anymore. Retrying..")
            time.sleep(1)
            driver.get(url)
            time_sleep(2, driver)
            finding_cards(driver)
        if not out_of_stock:
            pass
    except (TimeoutException, NoSuchElementException, ElementNotInteractableException):
        pass

    # If still in cart, attempting to click secure checkout button.
    try:
        available = driver.find_element_by_xpath("//*[@class='btn btn-primary btn-wide']").is_enabled()
        if available:
            time.sleep(1)
            driver_wait(driver, 'xpath', 'btn btn-primary btn-wide')
            print("Clicked Checkout Button in Cart.")
        if not available:
            print("Item Is Not In Cart Anymore. Retrying..")
            time.sleep(1)
            driver.get(url)
            time_sleep(2, driver)
            finding_cards(driver)
    except (TimeoutException, NoSuchElementException):
        print("Item Is Not In Cart Anymore. Retrying..")
        driver.get(url)
        time_sleep(3, driver)
        finding_cards(driver)

    # Logging Into Account.
    try:
        print("Attempting Sign-In.")
        wait.until(ec.visibility_of_element_located((By.ID, "labeled-input-signEmail")))
        password_field = driver.find_element_by_id("labeled-input-signEmail")
        time.sleep(1)
        password_field.send_keys(Keys.ENTER)
    except (NoSuchElementException, TimeoutException):
        print("Could Not Log Email Address.")

    try:
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
        wait.until(ec.visibility_of_element_located((By.XPATH, "//input[@class='form-text mask-cvv-4'][@type='text']")))
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
    print("driver quit.")
    driver.quit()


if __name__ == '__main__':
    driver = create_driver()
    finding_cards(driver)
