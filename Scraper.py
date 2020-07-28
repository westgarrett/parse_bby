import requests
from bs4 import BeautifulSoup
import regex
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from fake_useragent import UserAgent
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
import asyncio
import aiohttp
from Wrappers import function_timer


# This class encapsulates scraping tools for use on the Best Buy website.
class Scraper:
    ####################################################################################################################
    # Private Functions                                                                                                #
    ####################################################################################################################
    def __init__(self, url=""):
        print("Initializing a scraper object")
        self.url = url
        self.headers = {'User-Agent': 'Mozilla/5.0'}
        self.product_page_url = "https://www.bestbuy.com/site/searchpage.jsp?st="
        try:
            self.req = self._get_request()
        except Exception as e:
            print(f"\nCould not get request object due to exception: {e}")
            print("This happens when initiating a Scraper() object with no url parameter. It's fine.")
            pass
        try:
            self.contents = self._get_contents()
        except Exception as e:
            print(f"\nCould not get request object due to exception: {e}")
            print("This happens when requests fails to grab contents in the Scraper() initializer.")
            pass

    # For debugging
    def __str__(self):
        return f"Scraper object on {self.url}"

    # Private class method that returns the requests.get object for the url initialized with the Parser/Scraper object
    # the "headers" modifier disguises the parser/scraper as a user.

    def _get_request(self):
        return requests.get(self.url, headers=self.headers)

    # Returns the page contents using BeautifulSoup.
    def _get_contents(self):
        return BeautifulSoup(self.req.content, "html5lib")

    # Reruns _get_contents
    def _retry_get_contents(self):
        return self._get_contents()

    # Starts Selenium and returns a webdriver object
    @staticmethod
    def start_selenium():
        options = Options()
        profile = webdriver.FirefoxProfile()
        user_agent = UserAgent().random

        # Set the selenium instance to headless
        options.headless = True
        # Set UserAgent to a random one. Avoids automated scraper shutdowns
        profile.set_preference("general.useragent.override", user_agent)
        # Add the profile and options parameters to the selenium WebDriver
        driver = webdriver.Firefox(firefox_profile=profile, options=options)

        if options.headless:
            print(f"Starting a headless selenium browser")
        else:
            print(f"Starting a non-headless selenium browser")
        return driver

    @staticmethod
    def _wait_for_load_selenium(xpath, driver):
        wait = WebDriverWait(driver, 5)
        wait.until(EC.visibility_of_element_located((By.XPATH, xpath)))

    ####################################################################################################################
    # Get Functions                                                                                                    #
    ####################################################################################################################

    # Returns the connection status code of a get.
    def get_status_code(self):
        return self.req.status_code

    ####################################################################################################################
    # Get Functions for search pages                                                                                   #
    ####################################################################################################################

    # https://www.bestbuy.com/site/searchpage.jsp?st=*
    # Did not know you could do this.

    # Returns the link to each product on the given search page.
    def get_product_names(self):
        names = []
        name_divs = self.contents.find_all("h4", attrs={"class": "sku-header"})
        for name in name_divs:
            names.append(name.find_next().text)
        return names

    # Returns a list of product URLs present on the search page.
    def get_product_links(self):
        links = []
        link_divs = self.contents.find_all("h4", attrs={"class": "sku-header"})
        for link in link_divs:
            links.append(f"""https://www.bestbuy.com{link.find_next().get("href")}""")
        return links

    # Creates a dictionary that adds more Scraper objects with page contents with url as key
    def get_product_pages(self, urls):
        page_dict = {}
        for url in urls:
            page_dict[url] = Scraper(url)

        return page_dict

    # Returns the SKUs from the search results as a list object.
    def get_skus(self):
        skus = []
        sku_values = self.contents.find_all("li", attrs={"class": "sku-item"})
        for i in sku_values:
            skus.append(int(i.get("data-sku-id")))
        return skus

    def get_upcs(self):
        links = self.get_product_links()
        upcs = []
        # page_contents = asyncio.get_event_loop().run_until_complete(self.get_product_pages(links))
        page_contents = self.get_product_pages(links)
        # print(page_contents)
        for content in page_contents:
            upcs.append(self._find_upc(page_contents[content]))
            # upcs.append(asyncio.get_event_loop().run_until_complete(self._find_upc(page_contents[content])))
        return upcs

    # Finds UPCs in the page contents
    @staticmethod
    def _find_upc(page_content):
        print(f"Finding upc in: {page_content.url}")
        # find_all returns a list, isolate the only element in the list [0], find the parent, then find the next div
        # which contains the UPC.
        upc = page_content.contents.find_all(string=regex.compile("UPC"), limit=1)[0].parent.find_next("div").contents[
            0]
        return upc

    # Returns the number of search results on the page. For some reason, the best buy website sometimes returns an
    # (n - 1) result count. Not sure what the conditions are for that.
    def get_num_results(self):
        class Format:
            def __str__(self):
                return f"""You are parsing {num_results[0]} {num_results[1]}."""

            def __int__(self):
                return int(num_results[0])

            def __float__(self):
                return float(num_results[0])

        results_format = Format()
        num_results = self.contents.find("span", attrs={"item-count"}).text.split()
        num_results[0] = int(num_results[0])
        return results_format

    # Returns a list of URL page results for a given link
    def get_pages(self):
        page_elements = self.contents.find_all("a", attrs={"class": "trans-button page-number"})
        page_list = []
        for i in page_elements:
            page_list.append(i.get("href"))
        return page_list

    # Returns the number of pages of results
    def get_num_pages(self):
        return len(self.get_pages())

    # Returns the current page number. If there is only one page, returns 1
    def get_current_page(self):
        try:
            return int(self.contents.find(attrs={"class": "trans-button current-page-number"}).text)
        except AttributeError:
            return 1

    # Toggles the next page of results if the number of pages is more than 0. Most likely solution here is to create a
    # new Scraper object for each request.get() fetch.
    def get_next_page(self):
        page_list = self.get_pages()
        num_pages = len(page_list)
        count = 0
        for i in range(num_pages):
            self.url = page_list[i]
            req = self.req
            count += 1
            print(f"""Switching to page {i}""")

    # Toggles the url to the previous page value if current page is more than 1. Similar to get_next_page(). May be
    # beneficial to store Scraper objects.
    def get_previous_page(self):
        pass

    ####################################################################################################################
    # Get Functions for product pages                                                                                  #
    ####################################################################################################################

    # Get product name on product page
    def get_product_name_on_product_page(self):
        try:
            title = self.contents.find("div", attrs={"itemprop": "name"}).find_next("h1").text
        except Exception as e:
            print(f"get_product_name_on_product_page failed with Exception: {e}\n")
            title = ""
        return title

    # Get product name on product page with Selenium by xpath
    # WIP, currently results in "Unable to find element <xpath>"
    @staticmethod
    def get_product_name_on_product_page_selenium(driver):
        driver.implicitly_wait(5)
        WebDriverWait(driver, 5)
        title_element = driver.find_element_by_xpath('//*[@class="sku-title"]')
        return title_element.text

    # Gets the price of the page item.
    def get_prices(self):
        print(self.contents)
        prices = self.contents.find_all("div", attrs={"priceView-hero-price priceView-customer-price"})
        prices_list = []
        for i in prices:
            prices_list.append(float((i.find_next().text[1:]).replace(",", "")))
        return prices_list

    # If a product has a Specifications field for "Carrier Compatibility," return the element contents as a list.
    def get_carrier_compatibility(self):
        # find_all returns a list, isolate the only element in the list, find the parent, then find the next div
        # which contains the carrier compatibility
        count = 0
        try:
            comp = self.contents.find_all(string=regex.compile("Carrier Compatibility"), limit=1)[0].parent.find_next(
                "div").contents[0].split(",")
        except Exception as e:
            print("get_carrier_compatibility failed with Exception: {e}\n")
            comp = []
        return comp

    def is_available(self):
        is_unavailable = self.contents.find_all("button", attrs={"add-to-cart-button", "disabled"})
        if len(is_unavailable) > 0:
            return False
        return True

    @staticmethod
    # Finds the "Add to Cart" button and determines if it is disabled. Returns True if available, False otherwise
    # I think this is blocked in bestbuy.com/robots.txt
    def is_available_selenium(driver) -> bool:
        xpath = '//button[@class="add-to-cart-button"]'
        button = driver.find_element_by_xpath(xpath)
        button_text = button.text
        return button.is_enabled()

    # WIP, currently cannot find certain React-generated methods
    # @staticmethod
    # def get_carrier_compatibility_selenium(driver):
    #     comp = driver.find_element_by_xpath("//*[contains(text(), 'Carrier Compatibility')]")
    #     return comp
    ####################################################################################################################
    # Set Functions                                                                                                    #
    ####################################################################################################################

    # Set the page to a given page number. Must be between 1 and self.get_num_pages().
    def set_page(self):
        # scraper = Scraper()
        pass

    ####################################################################################################################
    # Error handling functions                                                                                         #
    ####################################################################################################################

    @staticmethod
    # Determines if no results are present from a given sku
    # Test SKU: 0000000
    def find_no_results_message_selenium(driver) -> bool:
        xpath = '//*[@class="no-results-message"]'
        if len(driver.find_elements_by_xpath(xpath)) > 0:
            return True
        return False

    @staticmethod
    # Determines if something goes wrong i.e. cannot figure out what the browser is asking.
    # Test "SKU": +
    def find_something_went_wrong_message_selenium(driver) -> bool:
        xpath = '//*[@class="heading VPT-title"]'
        if len(driver.find_elements_by_xpath(xpath)) > 0:
            return True
        return False

    # Returns a boolean. If no_results_message or something_went_wrong_message is present, return True because
    # there are no results.
    # If there is a catch condition, the presence indicates there are results, so if catch_condition return False
    @function_timer
    def no_results_flag(self, driver: webdriver, catch_condition: bool) -> bool:

        # Assume there is not an exception and there are no search results
        no_results = True
        went_wrong = True

        # If a catch condition is present (True), don't search for the next two exceptions to save resources (namely
        #   time)
        if catch_condition:
            return False

        if self.find_no_results_message_selenium(driver) > 0:
            print("No results found message present")
        else:
            no_results = False

        if self.find_something_went_wrong_message_selenium(driver):
            print("Something went wrong message present")
        else:
            went_wrong = False

        # Returns True if the no_results message is found or the something_went_wrong message is found.
        if no_results or went_wrong:
            return True
        return False

    ####################################################################################################################
    # Data cleaning functions                                                                                          #
    ####################################################################################################################

    @staticmethod
    def find_price(tag):
        # Regex to select pricing in a string
        regex_selector = r"(USD|EUR|€|\$|£)\s?(\d{1,}(?:[.,]\d{3})*(?:[.,]\d{2}))|(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?)\s?(USD|EUR)"
        matches = regex.compile(regex_selector)
        prices = list(matches.findall(tag))
        if len(prices) == 0:
            return 0
        # For some reason this regex returns ('$', '<price in number form>', '', '')
        # Saving the number to the list explicitly
        for i in range(len(prices)):
            prices[i] = f"{prices[i][1]}"
        return prices



