import bs4
import sys
import time
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, ElementNotInteractableException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager
from selenium.common.exceptions import WebDriverException

# Newegg credentials
password = 'your-password'
cvv = 'your-cvv'

# Twilio configuration
toNumber = 'your_phonenumber'
fromNumber = 'twilio_phonenumber'
accountSid = 'ssid'
authToken = 'authtoken'
client = Client(accountSid, authToken)

# Product Page
url = 'https://www.newegg.com/p/pl?d=RTX+3080&N=100007709%20601357282%204841&isdeptsrh=1'


def timeSleep(x, driver):
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


def createDriver():
    """Creating driver."""
    options = Options()
    options.headless = False  # Change To True if you dont want to see Firefox Browser.
    profile = webdriver.FirefoxProfile(r'C:\Users\Trebor\AppData\Roaming\Mozilla\Firefox\Profiles\kwftlp36.default-release')
    driver = webdriver.Firefox(profile, options=options, executable_path=GeckoDriverManager().install())
    return driver


def driverWait(driver, findType, selector):
    """Driver Wait Settings."""
    while True:
        if findType == 'css':
            try:
                driver.find_element_by_css_selector(selector).click()
                break
            except NoSuchElementException:
                driver.implicitly_wait(0.5)
        elif findType == 'name':
            try:
                driver.find_element_by_name(selector).click()
                break
            except NoSuchElementException:
                driver.implicitly_wait(0.5)


def findingCards(driver):
    """Scanning all cards."""
    # time.sleep(1)
    driver.get(url)
    while True:
        html = driver.page_source
        soup = bs4.BeautifulSoup(html, 'html.parser')
        wait = WebDriverWait(driver, 5)
        try:
            findAllCards = soup.find('button', {'class': 'btn btn-primary btn-mini'})
            if findAllCards:
                print(f'Button Found!: {findAllCards.get_text()}')

                # Clicking Add to Cart.
                time.sleep(1)
                driver.find_element_by_xpath("//*[@class='btn btn-primary btn-mini']").click()
                time.sleep(1)

                # Going To Cart.
                driver.get('https://secure.newegg.com/shop/cart')

                # Checking if item already sold out after clicking to cart.
                try:
                    outofstock = driver.find_element_by_xpath("//*[@class='btn btn-secondary']").is_enabled()
                    if outofstock:
                        driver.find_element_by_xpath("//*[@class='btn btn-secondary']").click()
                        print("Item Is Not In Cart Anymore. Retrying..")
                        timeSleep(1, driver)
                        driver.get(url)
                        timeSleep(2, driver)
                        findingCards(driver)
                        return
                except (TimeoutException, NoSuchElementException):
                    pass

                try:
                    available = driver.find_element_by_xpath("//*[@class='btn btn-primary btn-wide']").is_enabled()
                    if available:
                        driver.find_element_by_xpath("//*[@class='btn btn-primary btn-wide']").click()
                        print("Clicked Checkout Button in Cart.")
                        timeSleep(5, driver)
                except (TimeoutException, NoSuchElementException):
                    print("Item Is Not In Cart Anymore. Retrying..")
                    driver.get(url)
                    timeSleep(3, driver)
                    findingCards(driver)
                    return

                # Logging Into Account.
                try:
                    print("Attempting Sign-In.")
                    wait.until(EC.visibility_of_element_located((By.ID, "labeled-input-password")))
                    passwordField = driver.find_element_by_id("labeled-input-password")
                    time.sleep(1)
                    passwordField.send_keys(password)
                    passwordField.send_keys(Keys.ENTER)
                except (NoSuchElementException, TimeoutException):
                    print("Could Not Login To Account With Password.")

                # Clicking Continue Payment
                try:
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".layout-quarter")))
                    driver.find_elements_by_css_selector(".layout-quarter")[1].click()
                except (NoSuchElementException, TimeoutException, ElementNotInteractableException, IndexError, WebDriverException):
                    pass

                # Submit CVV Code(Must type CVV number.
                try:
                    print("Trying Credit Card CVV Number.")
                    wait.until(EC.visibility_of_element_located((By.XPATH, "//input[@class='form-text mask-cvv-4'][@type='text']")))
                    security_code = driver.find_element_by_xpath("//input[@class='form-text mask-cvv-4'][@type='text']")
                    time.sleep(1)
                    security_code.send_keys(Keys.BACK_SPACE + Keys.BACK_SPACE + Keys.BACK_SPACE + Keys.BACK_SPACE + cvv)
                except (AttributeError, NoSuchElementException, TimeoutException, ElementNotInteractableException):
                    print("Could Not Type CVV.")

                # Text Updates
                try:
                    driver.find_elements_by_css_selector(".form-checkbox-title")[1].click()
                except (NoSuchElementException, TimeoutException, ElementNotInteractableException, IndexError):
                    pass

                # Final Checkout
                try:
                    driver.find_elements_by_css_selector(".layout-quarter")[2].click()
                except (NoSuchElementException, TimeoutException, ElementNotInteractableException, IndexError):
                    pass

                try:
                    wait.until(EC.visibility_of_element_located((By.XPATH, "//*[@class='btn btn-primary btn-wide']")))
                    driver.find_element_by_xpath("//*[@class='btn btn-primary btn-wide']").click()
                except (NoSuchElementException, TimeoutException, ElementNotInteractableException):
                    print("Could Not proceed with Checkout."

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
        timeSleep(5, driver)


if __name__ == '__main__':
    driver = createDriver()
    findingCards(driver)
