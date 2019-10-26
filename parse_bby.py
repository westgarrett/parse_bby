import dependencies.dependencies as depends
import Scraper
import Parser


if __name__ == "__main__":
    api_key = str(input("Input the API key. If you don't have one, leave this prompt blank: "))
    url = str(input("Input the url you are parsing: "))

    # Uses API calls
    if api_key != "":
        print("This goes on to API calls")

    # Is scraped
    else:
        print("This goes on to be scraped")

        # Initialize Scraper object with the given url
        scraper = Scraper.Scraper(url)

        # Returns the request.get status code
        print(scraper.get_status_code())

        # Returns the number of page results
        # As a pretty string
        print(scraper.get_num_results())
        # As an integer
        print(int(scraper.get_num_results()))
        # As a float(if you're into that)
        print(float(scraper.get_num_results()))

        # Returns a list of skus on the page
        print(scraper.get_skus())

        # Returns a list of prices for each sku
        print(scraper.get_prices())

        # Returns the number of pages
        print(scraper.get_num_pages())

        # Returns the links to the next get_num_pages() pages
        print(scraper.get_pages())


