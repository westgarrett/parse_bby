import csv
from typing import TextIO

from Scraper import Scraper
from UNLScraper import UNLScraper
# from CarrierScraper import CarrierScraper
from Scraper import function_timer


class Saver:

    def __init__(self):
        self.field_names = ['ID', 'SKU', 'ProductName', 'Compatibility', 'ATT_new_price',
                            'ATT_upg_price', 'SPR_new_price', 'SPR_upg_price', 'VZW_new_price',
                            'VZW_upg_price', 'TMO_new_price', 'TMO_upg_price',
                            'Unactivated_price'
                            ]
        self.scraper = Scraper()
        self.index = 0

        self.phones = open("./outputFiles/phones.csv", "w", newline="")
        self.writer_obj = csv.DictWriter(self.phones, fieldnames=self.field_names, delimiter=",", quotechar='"',
                                         quoting=csv.QUOTE_MINIMAL)
        self.writer_obj.writeheader()

    ####################################################################################################################
    # Test functions                                                                                                   #
    ####################################################################################################################

    # Check if the page has no results. Encapsulation for clean writing function.
    # If this is used, it typically adds ~ 2.5 seconds to EACH request due to running a new selenium request each time.
    # Debugging only.
    @staticmethod
    def _no_results_check(scraper, driver):
        # Populate the driver object with the scraper url
        driver.get(scraper.url)
        # Check if the page has no results. If it doesn't have results, skip the sku and continue the loop
        no_results = scraper.no_results_flag(driver)
        return no_results

    ####################################################################################################################
    # Write functions                                                                                                  #
    ####################################################################################################################

    # Write to phones.csv with a given text file of skus.txt
    #         Int,String,String,Dict_of_doubles
    def write_unl_phones_csv(self):
        skus = open("./skuLists/unl_skus.txt", "r")
        # Phone activation prices are called with a javascript function, selenium is necessary
        driver = self.scraper.start_selenium()

        # For each sku, run a request with a new scraper object for each product page
        for sku in skus:
            sku = sku.strip()
            search_url = f"https://www.bestbuy.com/site/searchpage.jsp?st={sku}"
            unl_scraper = UNLScraper(search_url)
            # Returns a dictionary of activation prices
            pricing_dict = unl_scraper.get_activation_prices(sku, driver)
            print(pricing_dict)

            if pricing_dict == 0:
                print(f"SKU: {sku} does not exist on website. Terminate row.")
            else:

                product_name = unl_scraper.get_product_name_on_product_page()
                compatibility = unl_scraper.get_carrier_compatibility()

                # Create a dictionary to write a row to CSV
                row_dict = {"ID": self.index, "SKU": sku, "ProductName": product_name, "Compatibility": compatibility}

                # Merges the dictionary formed in get_activation_prices() to the row_dict dictionary
                row_dict.update(pricing_dict)
                self.writer_obj.writerow(row_dict)
                self.index += 1

                # I think the Scraper()._get_contents() method is causing RAM usage to spike really hard.
                # This should help a bit as none of the scraper objects are being reused.
                print("Deleting the scraper object")
                del unl_scraper

        skus.close()
        self.phones.close()
        driver.quit()

    # write to phones.csv
    def write_carrier_phones_csv(self):
        skus = open("./skuLists/carrier_skus.txt", "r")

        # Phone activation prices are called with a javascript function, selenium is necessary
        driver = self.scraper.start_selenium()

        for sku in skus:
            carrier_scraper = CarrierScraper(f"https://www.bestbuy.com/site/searchpage.jsp?st={sku}")
            # Check if a given sku garners a result
            no_results = carrier_scraper.no_results_flag(driver)
            if no_results:
                pass
            product_name = carrier_scraper.get_product_name_on_product_page_selenium()
            compatibility = carrier_scraper.get_carrier_compatibility()
            # Returns a dictionary of activation prices
            pricing_dict = carrier_scraper.get_activation_prices(sku, driver)

            if pricing_dict == 0:
                print("SKU does not exist on website. Terminate row.")
            else:
                # Create a dictionary to write a row to CSV
                row_dict = {"ID": self.index, "SKU": sku, "ProductName": product_name, "Compatibility": compatibility}

                # Merges the dictionary formed in get_activation_prices() to the row_dict dictionary
                row_dict.update(pricing_dict)
                self.writer_obj.writerow(row_dict)
                self.index += 1

        skus.close()
        self.phones.close()
        driver.quit()
