import csv
from typing import TextIO

from Scraper import Scraper
from UNLScraper import UNLScraper


class Saver:
    def __init__(self):
        self.field_names = ['ID', 'SKU', 'ProductName', 'Compatibility', 'ATT_new_price',
                            'ATT_upg_price', 'SPR_new_price', 'SPR_upg_price', 'VZW_new_price',
                            'VZW_upg_price', 'TMO_new_price', 'TMO_upg_price',
                            'Unactivated_price'
                            ]
        self.scraper = Scraper()

    ####################################################################################################################
    # Write functions                                                                                                  #
    ####################################################################################################################

    # Write to phones.csv with a given text file of skus.txt
    #         Int,String,String,Dict_of_doubles
    def write_phones_csv(self):
        skus = open("skus.txt", "r")
        phones = open("phones.csv", "w", newline="")

        writer_obj = csv.DictWriter(phones, fieldnames=self.field_names, delimiter=",", quotechar='"',
                                    quoting=csv.QUOTE_MINIMAL)
        writer_obj.writeheader()
        # Phone activation prices are called with a javascript function, selenium is necessary
        driver = self.scraper.start_selenium()

        # For each sku, run a request with a new scraper object for each product page
        index = 0
        for sku in skus:
            unl_scraper = UNLScraper(f"https://www.bestbuy.com/site/searchpage.jsp?st={sku}")
            # scraper = Scraper(f"https://www.bestbuy.com/site/searchpage.jsp?st={sku}")
            product_name = unl_scraper.get_product_name_on_product_page()
            compatibility = unl_scraper.get_carrier_compatibility()
            # Returns a dictionary of activation prices
            pricing_dict = unl_scraper.get_activation_prices(sku, driver)

            # Create a dictionary to write a row to CSV
            row_dict = {}
            row_dict["ID"] = index
            row_dict["SKU"] = sku
            row_dict["ProductName"] = product_name
            row_dict["Compatibility"] = compatibility

            # Merges the dictionary formed in get_activation_prices() to the row_dict dictionary
            row_dict.update(pricing_dict)
            writer_obj.writerow(row_dict)
            index += 1

        skus.close()
        phones.close()
        driver.quit()
