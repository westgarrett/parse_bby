import dependencies.dependencies as depends
import requests
from bs4 import BeautifulSoup
import selenium
import html5lib
import validators
import regex
import threading
from validator_collection import checkers
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from regex import compile
import asyncio
import aiohttp


# This class encapsulates scraping tools for use on the Best Buy website.
class Scraper:
    ####################################################################################################################
    # Private Functions                                                                                                #
    ####################################################################################################################
    def __init__(self, url):
        self.url = url
        self.headers = {'User-Agent': 'Mozilla/5.0'}
        self.req = self._get_request()
        self.contents = self._get_contents()

    # Private class method that returns the requests.get object for the url initialized with the Parser/Scraper object
    # the "headers" modifier disguises the parser/scraper as a user.
    def _get_request(self):
        return requests.get(self.url, headers=self.headers)

    # Returns the page contents using BeautifulSoup.
    def _get_contents(self):
        return BeautifulSoup(self.req.content, "html5lib")

    ####################################################################################################################
    # Get Functions                                                                                                    #
    ####################################################################################################################

    # Returns the connection status code of a get.
    def get_status_code(self):
        return self.req.status_code

    # Returns the link to each product on the given page.
    def get_product_names(self):
        names = []
        name_divs = self.contents.find_all("h4", attrs={"class": "sku-header"})
        for name in name_divs:
            names.append(name.find_next().text)
        return names

    # Returns a list of product URLs present on the page.
    def get_product_links(self):
        links = []
        link_divs = self.contents.find_all("h4", attrs={"class": "sku-header"})
        for link in link_divs:
            links.append(f"""https://www.bestbuy.com{link.find_next().get("href")}""")
        return links

    # Accesses each item page and appends the "UPC" field to a list. Returns the list of UPCs from the search results.
    # Runs each get request asynchronously using aiohttp.
    async def get_product_pages(self, urls):
        async with aiohttp.ClientSession() as session:
            page_contents = []
            for url in urls:
                print(f"Gathering information from {url}")
                page_contents.append(asyncio.ensure_future(self._get_product_page(session, url)))
            await asyncio.gather(*page_contents, return_exceptions=True)
        return page_contents

    async def _get_product_page(self, session, url):
        async with session.get(url, headers=self.headers) as response:
            return await response.text()

    # Asynchronously finds UPCs in the page contents
    async def _find_upc(self, page_content):
        return await page_content.find_all(string=regex.compile("UPC"), limit=1)

    def get_upcs(self):
        links = self.get_product_links()
        upcs = []
        page_contents = asyncio.get_event_loop().run_until_complete(self.get_product_pages(links))
        print(page_contents)
        for content in page_contents:
            upcs.append(asyncio.get_event_loop().run_until_complete(self._find_upc(content)))
        return upcs

    # Returns the SKUs from the search results as a list object.
    def get_skus(self):
        skus = []
        sku_values = self.contents.find_all("li", attrs={"class": "sku-item"})
        for i in sku_values:
            skus.append(int(i.get("data-sku-id")))
        return skus

    # Gets the price of the page item.
    def get_prices(self):
        prices = self.contents.find_all("div", attrs={"priceView-hero-price priceView-customer-price"})
        prices_list = []
        for i in prices:
            prices_list.append(float(i.find_next().text[1:]))
        return prices_list

    # Returns the number of search results on the page. For some reason, the best buy website sometimes returns an  .
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
    # Set Functions                                                                                                    #
    ####################################################################################################################

    # Set the page to a given page number. Must be between 1 and self.get_num_pages()
    def set_page(self):
        pass
