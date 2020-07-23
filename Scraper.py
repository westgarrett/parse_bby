import csv

import requests
from bs4 import BeautifulSoup
from requests_html import HTMLSession
import time
import selenium
import html5lib
import validators
import regex
import threading

from requests import HTTPError
from validator_collection import checkers
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
from regex import compile
import asyncio
import aiohttp


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

    # Starts Selenium and returns a webdriver object
    @staticmethod
    def start_selenium():
        options = Options()
        options.headless = False
        driver = webdriver.Firefox(options=options)

        print("Starting a headless selenium browser")
        return driver

    # Clicks "<element>" on a page using Selenium and returns the information in "<name>"
    # Deprecated, keeping for formatting reference
    def _click_element(self, element, name):
        driver = self.start_selenium()
        driver.get(self.url)

        # Deprecated
        if name == "UPC":
            # Wait to see the button before trying to click it
            try:
                button = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, '//button[@data-track["Specifications"]]')))
            finally:
                button.click()
            print(button)
            row_values = driver.find_elements_by_xpath('//div[@class["title-container"]]')
            # for i in row_values:
            #     try:
            #         print(int(i.text))
            #     except Exception:
            #         pass
            # driver.quit()

        return row_values

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
        title = self.contents.find("div", attrs={"itemprop": "name"}).find_next("h1").text
        return title

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
        comp = self.contents.find_all(string=regex.compile("Carrier Compatibility"), limit=1)[0].parent.find_next(
            "div").contents[0].split(",")
        return comp

    ####################################################################################################################
    # Set Functions                                                                                                    #
    ####################################################################################################################

    # Set the page to a given page number. Must be between 1 and self.get_num_pages().
    def set_page(self):
        # scraper = Scraper()
        pass


