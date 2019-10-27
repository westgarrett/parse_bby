import dependencies.dependencies as depends


# This class encapsulates scraping tools for use on the Best Buy website.
class Scraper:
    def __init__(self, url):
        self.url = url

    # Returns the connection status code of a get.
    def get_status_code(self):
        return self._get_request().status_code

    # Private class method that returns the requests.get object for the url initialized with the Parser/Scraper object
    # the "headers" modifier disguises the parser/scraper as a user.
    def _get_request(self):
        return depends.requests.get(self.url, headers={'User-Agent': 'Mozilla/5.0'})

    # Returns the page contents using BeautifulSoup.
    def get_contents(self):
        req = self._get_request()
        contents = depends.BeautifulSoup(req.content, "html5lib")
        return contents

    # Recursively accesses each item page, accesses "Specifications" if present, and appends the "Quantity" field to a
    # list. Returns the quantities of each item at a set location (future method?).
    def get_quantities(self):
        pass

    # Returns the link to each product on the given page.
    def get_product_names(self):
        names = []
        name_divs = self.get_contents().find_all("h4", attrs={"class": "sku-header"})
        for name in name_divs:
            names.append(name.find_next().text)
        return names

    # Returns a list of product URLs present on the page.
    def get_product_links(self):
        links = []
        link_divs = self.get_contents().find_all("h4", attrs={"class": "sku-header"})
        for link in link_divs:
            links.append(f"""https://www.bestbuy.com{link.find_next().get("href")}""")
        return links

    # Accesses each item page and appends the "UPC" field to a list. Returns the list of UPCs from the search results.
    # This method take a while to run, be patient!
    def get_upcs(self):
        links = self.get_product_links()
        upcs = []
        count = 0
        for url in links:
            count += 1
            print(f"""Checking link number {count}""")
            self.url = url
            code = int(self.get_status_code())
            if code == 200:
                contents = self.get_contents().find_all(string=depends.compile("UPC"), limit=1)
                for i in contents:
                    upcs.append(i.find_next().text)
        return upcs

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
        num_results = self.get_contents().find("span", attrs={"item-count"}).text.split()
        num_results[0] = int(num_results[0])
        return results_format

    # Returns a list of URL page results for a given link
    def get_pages(self):
        page_elements = self.get_contents().find_all("a", attrs={"class": "trans-button page-number"})
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
            return int(self.get_contents().find(attrs={"class": "trans-button current-page-number"}).text)
        except AttributeError:
            return 1

    # Toggles the next page of results if the number of pages is more than 0
    def get_next_page(self):
        page_list = self.get_pages()
        num_pages = len(page_list)
        count = 0
        for i in range(num_pages):
            self.url = page_list[i]
            req = self._get_request()
            count += 1
            print(f"""Switching to page {i}""")

    # Toggles the url to the previous page value if current page is more than 1.
    def get_previous_page(self):
        pass