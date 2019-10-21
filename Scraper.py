import dependencies.dependencies as depends


# This class encapsulates scraping tools for use on the best buy website
class Scraper:
    def __init__(self, url):
        self.url = url

    # Gets the price of the page item.
    def get_prices(self):
        prices = self.get_contents().find_all("div", attrs={"priceView-hero-price priceView-customer-price"})
        prices_list = []
        for i in prices:
            prices_list.append(i.find_next().text)
        return prices_list

    # Returns the connection status code of a get
    def get_status_code(self):
        return self._get_request().status_code

    # Returns the requests.get object for the url initialized with the Parser/Scraper object
    # the "headers" modifier disguises the parser/scraper as a user
    def _get_request(self):
        return depends.requests.get(self.url, headers={'User-Agent': 'Mozilla/5.0'})

    # Returns the page contents using BeautifulSoup
    def get_contents(self):
        req = self._get_request()
        contents = depends.BeautifulSoup(req.content, "html5lib")
        return contents

    # Returns the quantities of each item at a set location. Must use selenium to open each item link
    def get_quantities(self):
        pass

    # Returns a list of UPCs from the search results. Must use selenium to open each item
    def get_upcs(self):
        pass

    # Returns a list of SKUs from the search results
    def get_skus(self):
        skus = []
        sku_values = self.get_contents().find_all("li", attrs={"class": "sku-item"})
        for i in sku_values:
            skus.append(i.get("data-sku-id"))
        return skus

    # Returns the number of search results on the page. If more than 25, selenium must be used to list additional
    # results. For some reason, the best buy website sometimes returns an  (n - 1) result count.
    def get_num_results(self):
        num_results = self.get_contents().find("span", attrs={"item-count"}).text.split()
        num = int(num_results[0]) + 1
        num_results[0] = num
        return "You are parsing " + str(num_results[0]) + " " + num_results[1] + "."

