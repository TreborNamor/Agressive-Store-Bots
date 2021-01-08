import bs4
import sys
import time
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, ElementNotInteractableException, TimeoutException, WebDriverException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.chrome import ChromeDriverManager


# Twilio configuration
toNumber = 'your_phonenumber'
fromNumber = 'twilio_phonenumber'
accountSid = 'ssid'
authToken = 'authtoken'
client = Client(accountSid, authToken)

# Product Page
url = 'https://www.bestbuy.com/site/searchpage.jsp?_dyncharset=UTF-8&id=pcat17071&iht=y&keys=keys&ks=960&list=n&qp=gpusv_facet%3DGraphics%20Processing%20Unit%20(GPU)~NVIDIA%20GeForce%20RTX%203070%5Egpusv_facet%3DGraphics%20Processing%20Unit%20(GPU)~NVIDIA%20GeForce%20RTX%203080&sc=Global&st=rtx%203080%203070&type=page&usc=All%20Categories'


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
                driver.implicitly_wait(0.2)
        elif findType == 'name':
            try:
                driver.find_element_by_name(selector).click()
                break
            except NoSuchElementException:
                driver.implicitly_wait(0.2)


def findingCards(driver):
    """Scanning all cards."""
    driver.get(url)
    while True:
        html = driver.page_source
        soup = bs4.BeautifulSoup(html, 'html.parser')
        wait = WebDriverWait(driver, 15)
        wait2 = WebDriverWait(driver, 2)
        preorderwait = WebDriverWait(driver, 300)
        try:
            findAllCards = soup.find('button', {'class': 'btn btn-secondary btn-sm btn-block add-to-cart-button'})
            if findAllCards:
                print(f'Button Found!: {findAllCards.get_text()}')

                # Queue System Logic. It is a 3 click process.
                try:
                    # Product Found, clicking "add to cart" button. (Page 1 - List of all RTX Products Page)
                    time.sleep(1)
                    driverWait(driver, 'css', '.add-to-cart-button') # this is the code that clicks add to cart.
                    timeSleep(2, driver)

                    # Entering Queue: Clicking "add to cart" 2nd time to enter queue. (Page 2 - Specific RTX Card Page)
                    preorderwait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".add-to-cart-button")))
                    driverWait(driver, 'css', '.add-to-cart-button') # this is the code that clicks add to cart.
                    time.sleep(5)

                    # In queue, waiting for "add to cart" button to turn clickable again. (page 2)
                    preorderwait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".add-to-cart-button"))) # this will wait until button is clickable.
                    time.sleep(2)
                    driverWait(driver, 'css', '.add-to-cart-button') # this is the code that clicks add to cart.
                    time.sleep(2)

                except (NoSuchElementException, TimeoutException):
                    pass

                # Going To Cart Process.
                driver.get('https://www.bestbuy.com/cart')

                # Checking if item is still in cart.
                try:
                    wait.until(EC.presence_of_element_located((By.XPATH, "//*[@class='btn btn-lg btn-block btn-primary']")))
                    time.sleep(1)
                    driver.find_element_by_xpath("//*[@class='btn btn-lg btn-block btn-primary']").click()
                    print("Item Is Still In Cart.")
                except (NoSuchElementException, TimeoutException):
                    print("Item is not in cart anymore. Retrying..")
                    timeSleep(3, driver)
                    findingCards(driver)
                    return

                # Logging Into Account.
                print("Attempting to Login.")

                # Click Shipping Option. (If Available)
                try:
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#fulfillment_1losStandard0")))
                    time.sleep(1)
                    driverWait(driver, 'css', '#fulfillment_1losStandard0')
                    print("Clicking Shipping Option.")
                except (NoSuchElementException, TimeoutException):
                    pass

                # Trying CVV
                try:
                    print("\nTrying CVV Number.\n")
                    security_code = driver.find_element_by_id("credit-card-cvv")
                    time.sleep(1)
                    security_code.send_keys("123")  # You can enter your CVV number here.
                except (NoSuchElementException, TimeoutException):
                    pass

                # Bestbuy Text Updates.
                try:
                    wait2.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#text-updates")))
                    driverWait(driver, 'css', '#text-updates')
                    print("Selecting Text Updates.")
                except (NoSuchElementException, TimeoutException):
                    pass

                # Final Checkout.
                try:
                    wait2.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".btn-primary")))
                    driverWait(driver, 'css', '.btn-primary')
                except (NoSuchElementException, TimeoutException, ElementNotInteractableException) as error:
                    try:
                        wait2.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".btn-secondary")))
                        driverWait(driver, 'css', '.btn-secondary')
                        timeSleep(5, driver)
                        wait2.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".btn-primary")))
                        time.sleep(1)
                        driverWait(driver, 'css', '.btn-primary')
                    except (NoSuchElementException, TimeoutException, ElementNotInteractableException) as error:
                        print("Could Not Complete Checkout.")

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
            else:
                pass

        except (NoSuchElementException, TimeoutException, WebDriverException):
            pass
        timeSleep(2, driver)


if __name__ == '__main__':
    driver = createDriver()
    findingCards(driver)
