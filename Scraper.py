import dependencies.dependencies as depends


# This class encapsulates scraping tools for use on the best buy website.
class Scraper:
    def __init__(self, url):
        self.url = url

    # Returns the connection status code of a get.
    def get_status_code(self):
        return self._get_request().status_code

    # Returns the requests.get object for the url initialized with the Parser/Scraper object
    # the "headers" modifier disguises the parser/scraper as a user.
    def _get_request(self):
        return depends.requests.get(self.url, headers={'User-Agent': 'Mozilla/5.0'})

    # Returns the page contents using BeautifulSoup.
    def get_contents(self):
        req = self._get_request()
        contents = depends.BeautifulSoup(req.content, "html5lib")
        return contents

    # Returns the quantities of each item at a set location. Must use selenium to open each item link.
    def get_quantities(self):
        pass

    # Returns a list of UPCs from the search results. Must use selenium to open each item.
    def get_upcs(self):
        pass

    # Returns the SKUs from the search results as a list object.
    def get_skus(self):
        skus = []
        sku_values = self.get_contents().find_all("li", attrs={"class": "sku-item"})
        for i in sku_values:
            skus.append(int(i.get("data-sku-id")))
        return skus

    # Gets the price of the page item.
    def get_prices(self):
        prices = self.get_contents().find_all("div", attrs={"priceView-hero-price priceView-customer-price"})
        prices_list = []
        for i in prices:
            prices_list.append(float(i.find_next().text[1:]))
        return prices_list

    # Returns the number of search results on the page. If more than 25, selenium must be used to list additional
    # results. For some reason, the best buy website sometimes returns an  (n - 1) result count. Not sure what the
    # conditions are for that
    def get_num_results(self):
        class Format:
            def __str__(self):
                return f"""You are parsing {num_results[0]} {num_results[1]}."""

            def __int__(self):
                return int(num_results[0])

            def __float__(self):
                return float(num_results[0])

        results_format = Format()
        num_results = self.get_contents().find("span", attrs={"item-count"}).text.split()
        num_results[0] = int(num_results[0])
        return results_format

    # Returns a list of page results for a given link
    def get_pages(self):
        page_elements = self.get_contents().find_all("a", attrs={"class": "trans-button page-number"})
        page_list = []
        for i in page_elements:
            page_list.append(i.get("href"))
        return page_list

    # Returns the number of pages of results
    def get_num_pages(self):
        return len(self.get_pages())

    # Returns the next page of results if the number of results is more than 25, or there are page links present
    # at the end of the page due to the bug listed in the get_num_results() method notes.
    def get_next_page(self):
        if int(self.get_num_results()) > 25:
            driver = depends.webdriver.Firefox()
            driver.get(self.url)
            pages = driver.find_element_by_class_name("paging-list")
