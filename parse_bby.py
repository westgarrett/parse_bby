import time

from Saver import Saver
from Scraper import Scraper


def enter_url():
    url = str(input("Input the url you are parsing: "))
    return url

def library_methods():
    # Returns the request.get status code
    print(scraper.get_status_code())

    # # Returns the number of page results
    # # As a pretty string
    # print(scraper.get_num_results())
    # # As an integer
    # print(int(scraper.get_num_results()))
    # # As a float (if you're into that)
    # print(float(scraper.get_num_results()))

    # Returns a list of skus on a search page
    print(scraper.get_skus())

    # Returns a list of prices for each sku
    print(scraper.get_prices())

    # Returns the number of pages
    print(scraper.get_num_pages())

    # Returns the links to the next get_num_pages() pages
    print(scraper.get_pages())

    # Returns the names of all products on a given page
    print(scraper.get_product_names())

    # Returns a list of all the links on a given page
    print(scraper.get_product_links())

    # Returns a list of all UPCs of products on a given page
    print(scraper.get_upcs())

    # Returns the current page of results
    print(scraper.get_current_page())

if __name__ == "__main__":
    url = ""

    # User-supplied URL
    # while url == "":
    #     url = enter_url()
    # print(f"Scraping {url}")
    # print(scraper.get_status_code())

    # Initialize Scraper object with the given url (optional)
    scraper = Scraper()

    t = time.time()
    saver = Saver()
    saver.write_unl_phones_csv()
    print(time.time() - t)
