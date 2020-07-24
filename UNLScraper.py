import time

from bs4 import BeautifulSoup
from regex import regex
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.action_chains import ActionChains
from Scraper import Scraper, function_timer


class UNLScraper(Scraper):

    def __init__(self, url=""):
        super().__init__(url)
        self.contents = self._get_contents()
        self.driver = None

    ####################################################################################################################
    # Functions for unlocked phone pages                                                                               #
    ####################################################################################################################

    # Uses python requests .content attribute. Most I've tried have failed eventually, so this should be somewhere
    # to look if activation prices suddenly fail in line_activation_available
    @staticmethod
    def find_activation_type_button(page_content, activation_type):
        return page_content.find("button", attrs={"data-track": f"{activation_type}"})

    @staticmethod
    def contains_disclaimer(tag):
        if "Starting at" in tag:
            return True
        return False

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
            prices[i] = prices[i][1]
        return prices

    # If check_price_presence returns 0 (no prices), navigate to product page to grab pricing.
    # Added WebDriverWait function because I keep getting a stale element reference error
    def find_carrier_and_unlocked_price_if_only_one_carrier_promo_selenium(self, driver, sku):
        driver.get(f"{self.product_page_url}{sku}")
        driver.implicitly_wait(5)

        activation_xpath = '//*[@data-track="adprice-1m-"]'
        WebDriverWait(driver, 5)#.until(driver.find_element_by_xpath(activation_xpath))
        activation_price_element = driver.find_element_by_xpath(activation_xpath)
        activation_price = self.find_price(activation_price_element.text)[0]

        unlocked_xpath = '//*[@data-track="adprice-unactivated"]'
        WebDriverWait(driver, 5)#.until(driver.find_element_by_xpath(unlocked_xpath))
        unlocked_price_element = driver.find_element_by_xpath(unlocked_xpath)
        unlocked_price = self.find_price(unlocked_price_element.text)[0]

        return [activation_price, unlocked_price]

    @staticmethod
    def find_carrier_price_selenium(company, driver):
        xpath = f'//*[@data-track="{company}"]'
        return driver.find_element_by_xpath(xpath)

    @staticmethod
    def find_disclaimer_selenium(driver):
        xpath = f'//*[@class="carriers-page__disclaimer"]'
        return driver.find_element_by_xpath(f'//*[@class="carriers-page__disclaimer"]')

    @staticmethod
    def find_carrier_activation_button_selenium(company, driver):
        xpath = f'//*[@data-track="{company}"]'
        return driver.find_element_by_xpath(f'//*[@data-track="{company}"]')

    @staticmethod
    def find_carrier_continue_button_selenium(driver):
        xpath = '//*[@data-track="continue"]'
        return driver.find_element_by_xpath('//*[@data-track="continue"]')

    @staticmethod
    def find_no_trade_in_button_selenium(driver):
        xpath = '//*[@data-track="trade-in-optin-no"]'
        return driver.find_element_by_xpath('//*[@data-track="trade-in-optin-no"]')

    @staticmethod
    # Determines if no results are present from a given sku
    # Test SKU: 0000000
    def find_no_results_message_selenium(driver):
        xpath = '//*[@class="no-results-message"]'
        return driver.find_elements_by_xpath(xpath)

    @staticmethod
    # Determines if something goes wrong i.e. cannot figure out what the browser is asking.
    # Test "SKU": +
    def find_something_went_wrong_message_selenium(driver):
        xpath = '//*[@class="heading VPT-title"]'
        return driver.find_elements_by_xpath(xpath)

    # Finds the img tag holding the phone image on the given page. A good check if there are results for carrier
    # options.
    @staticmethod
    def find_image_on_carrier_activation_page(driver):
        xpath = '//*[@class="carriers-page__device-image"]'
        return driver.find_elements_by_xpath(xpath)

    # Returns a boolean. If no_results_message or something_went_wrong_message is present, return True because
    # there are no results.
    @function_timer
    def no_results_flag(self, driver):
        # Assume that there are no search results
        no_results = True
        went_wrong = True

        # Looks for "No results found" message
        # try:
        #     self.find_no_results_message_selenium(driver)
        #     print("No results found message present")
        # except NoSuchElementException:
        #     # There are results
        #     no_results = False

        # Looks for "Something went wrong" message
        # try:
        #     self.find_something_went_wrong_message_selenium(driver)
        #     print("Something went wrong message present")
        # except NoSuchElementException:
        #     # Nothing went wrong
        #     went_wrong = False

        # If the image is present, "no results found" message and "something went wrong" message are not present
        # This is an error catch. If there is a rogue SKU, it will take longer than a non-rogue SKU.
        if len(self.find_image_on_carrier_activation_page(driver)) > 0:
            return False

        if len(self.find_no_results_message_selenium(driver)) > 0:
            print("No results found message present")
        else:
            no_results = False

        if len(self.find_something_went_wrong_message_selenium(driver)) > 0:
            print("Something went wrong message present")
        else:
            went_wrong = False

        # Returns True if the no_results message is found or the something_went_wrong message is found.
        if no_results or went_wrong:
            return True
        return False

    # Opens a new tab in selenium and navigates a few buttons to see if upgrade and add-lines are enabled for a sku
    def line_activation_available(self, sku, company, driver):
        upg_is_available = new_is_available = False
        activation_options_link = f"https://www.bestbuy.com/wireless/transaction-types/render/transactions/vez?numberOfPayments=1&purchaseType=FULL_SRP&skuId={sku}"

        # Open the page in a new tab in selenium to avoid ram hogging
        driver.execute_script("window.open()")
        # Switch to the new window
        driver.switch_to.window(driver.window_handles[1])
        # Get new page
        driver.get(activation_options_link)

        self._wait_for_load_selenium(f'//*[@data-track="{company}"]', driver)

        # Navigate through prompts to trigger javascript
        carrier_button = self.find_carrier_activation_button_selenium(company, driver)
        carrier_button.click()

        # Continue button
        continue_button = self.find_carrier_continue_button_selenium(driver)
        continue_button.click()

        self._wait_for_load_selenium('//*[@data-track="trade-in-optin-no"]', driver)

        # No trade in button
        no_trade_in_button = self.find_no_trade_in_button_selenium(driver)
        no_trade_in_button.click()

        self._wait_for_load_selenium('//*[@class="transaction-types"]', driver)

        html = driver.execute_script("return document.documentElement.innerHTML;")
        page_content = BeautifulSoup(html, "html5lib")

        upgrade_button = self.find_activation_type_button(page_content, "upgrade")
        new_line_button = self.find_activation_type_button(page_content, "add-a-line")

        if upgrade_button is not None:
            upg_is_available = True
        if new_line_button is not None:
            new_is_available = True

        # Close the new window
        driver.close()
        # time.sleep(3)
        # Switch WebDriver back to main page when finished
        driver.switch_to.window(driver.window_handles[0])

        return [upg_is_available, new_is_available]

    # If a product has activation pricing, return them in a dictionary with keys:
    # ATT_new_price,ATT_upg_price,SPR_new_price,SPR_upg_price,VZW_new_price,VZW_upg_price,TMO_new_price,TMO_upg_price,Unactivated_price
    # Currently only works if there is one "disclaimer" tag. Currently no offers to add additional functionality
    @function_timer
    def get_activation_prices(self, sku, driver):
        # Adds WebDriver as a property to the class. May make things easier. Maybe harder. We'll see.
        # self.driver = driver
        price_page = f"https://www.bestbuy.com/wireless/transaction-types/render/carriers?numberOfPayments=1&purchaseType=FULL_SRP&skuId={sku}"
        # Must use a Selenium driver because the pricing is the result of a javascript function
        driver.get(price_page)

        # Grabs the innerHTML generated by javascript
        # html = driver.execute_script("return document.documentElement.innerHTML;")
        # page_content = BeautifulSoup(html, "html5lib")

        # Make sure to quit out of the selenium driver after the script is through
        # if disclaimer is present, there is a different pricing for upg/new line
        vzw_upg = vzw_new = att_upg = att_new = spr_upg = spr_new = tmo_upg = tmo_new = unactivated = "-1"
        disclaimer = disclaimer_price = None
        exception_price_list = []

        # Check if a search term does not result in a "Item not found" page
        no_results = self.no_results_flag(driver)

        if no_results:
            print(f"A no result flag has been triggered in get_activation_prices with sku: {sku}")
            return 0

        try:
            try:
                disclaimer = self.find_disclaimer_selenium(driver)
                disclaimer_price = self.find_price(disclaimer.text)
            except Exception as e:
                print(f"Exception for disclaimer for sku {sku}: {e}")
                if disclaimer is None:
                    print(f"Disclaimer not present, presumably Upg == New for {sku} on all carriers")
                    print("\tAT&T is a notable exception because they don't like unlocked upgrade activations")

            try:
                vzw_price_element = self.find_carrier_price_selenium("Verizon", driver)
                # Attempting to avoid stale element exceptions
                vzw_price_element_string = vzw_price_element.text
                # Test if price has more than one element. If price has 0 elements, find_price returns 0, 0[0] returns
                # a TypeError
                try:
                    vzw_price = self.find_price(vzw_price_element_string)[0]
                except TypeError:
                    exception_price_list = self.find_carrier_and_unlocked_price_if_only_one_carrier_promo_selenium(driver, sku)
                    vzw_price, unactivated = exception_price_list[0], exception_price_list[1]
                verizon_element_present = True
            except Exception:
                print(f"Verizon activation not available for {sku}")
                verizon_element_present = False

            try:
                att_price_element = self.find_carrier_price_selenium("ATT", driver)
                # Attempting to avoid stale element exceptions
                att_price_element_string = att_price_element.text
                # Test if price has more than one element. If price has 0 elements, find_price returns 0, 0[0] returns
                # a TypeError
                try:
                    att_price = self.find_price(att_price_element_string)[0]
                except TypeError:
                    exception_price_list = self.find_carrier_and_unlocked_price_if_only_one_carrier_promo_selenium(driver, sku)
                    att_price, unactivated = exception_price_list[0], exception_price_list[1]
                att_element_present = True
            except Exception:
                print(f"AT&T activation not available for {sku}")
                att_element_present = False

            try:
                spr_price_element = self.find_carrier_price_selenium("Sprint", driver)
                spr_price_element_string = spr_price_element.text
                # Test if price has more than one element. If price has 0 elements, find_price returns 0, 0[0] returns
                # a TypeError
                try:
                    spr_price = self.find_price(spr_price_element_string)[0]
                except TypeError:
                    exception_price_list = self.find_carrier_and_unlocked_price_if_only_one_carrier_promo_selenium(driver, sku)
                    spr_price, unactivated = exception_price_list[0], exception_price_list[1]
                spr_element_present = True
            except Exception:
                print(f"Sprint activation not available for {sku}")
                spr_element_present = False

            # try:
            #     tmo_price_element = self.find_carrier_price_selenium("TMobile", driver)
            #     tmo_price_element_string = tmo_price_element.text
            #     # Test if price has more than one element. If price has 0 elements, find_price returns 0, 0[0] returns
            #     # a TypeError
            #     try:
            #         tmo_price = self.find_price(tmo_price_element_string)[0]
            #     except TypeError:
            #         exception_price_list = self.find_carrier_and_unlocked_price_if_only_one_carrier_promo_selenium(driver, sku)
            #         tmo_price, unactivated = exception_price_list[0], exception_price_list[1]
            #     tmo_element_present = True
            # except Exception:
            #     print(f"T-Mobile activation not available for {sku}")
            #     tmo_element_present = False

            try:
                unactivated_element = self.find_carrier_price_selenium("activate-later", driver)
                if len(exception_price_list) > 0:
                    pass
                else:
                    unactivated = self.find_price(unactivated_element.text)[0]
                unactivated_element_present = True
            except Exception:
                unactivated_element_present = False

            # Verizon
            if verizon_element_present:
                if self.contains_disclaimer(vzw_price_element_string):
                    print("vzw has disclaimer")
                    vzw_new = disclaimer_price[0]
                    vzw_upg = disclaimer_price[1]
                # Check if allowing unlocked activations on new lines and upgrades. Not necessary if contains_disclaimer
                else:
                    flag = self.line_activation_available(sku, "Verizon", driver)
                    vzw_upg_flag = flag[0]
                    vzw_new_flag = flag[1]
                    if vzw_new_flag and vzw_upg_flag:
                        vzw_new = vzw_upg = vzw_price
                    elif vzw_new_flag and not vzw_upg_flag:
                        vzw_new = vzw_price
                    else:
                        vzw_upg = vzw_price

            # AT&T
            if att_element_present:
                if self.contains_disclaimer(att_price_element_string):
                    print("att has disclaimer")
                    att_new = disclaimer_price[0]
                    att_upg = disclaimer_price[1]
                # Check if allowing unlocked activations on new lines and upgrades.
                else:
                    flag = self.line_activation_available(sku, "ATT", driver)
                    att_upg_flag = flag[0]
                    att_new_flag = flag[1]
                    if att_upg_flag and att_new_flag:
                        att_new = att_upg = att_price
                    elif att_new_flag and not att_upg_flag:
                        att_new = att_price
                    else:
                        att_upg = att_price

            # Sprint
            if spr_element_present:
                if self.contains_disclaimer(spr_price_element_string):
                    print("spr has disclaimer")
                    spr_new = disclaimer_price[0]
                    spr_upg = disclaimer_price[1]
                else:
                    flag = self.line_activation_available(sku, "Sprint", driver)
                    spr_upg_flag = flag[0]
                    spr_new_flag = flag[1]
                    if spr_upg_flag and spr_new_flag:
                        spr_new = spr_upg = spr_price
                    elif spr_new_flag and not spr_upg_flag:
                        spr_new = spr_price
                    else:
                        spr_upg = spr_price

            # T-Mobile
            # if tmo_element_present:
            #     if self.contains_disclaimer(tmo_price_element_string):
            #         print("tmo has disclaimer")
            #         tmo_new = disclaimer_price[0]
            #         tmo_upg = disclaimer_price[1]
            #     else:
            #         flag = self.line_activation_available(sku, "TMobile", driver)
            #         tmo_upg_flag = flag[0]
            #         tmo_new_flag = flag[1]
            #         if tmo_upg_flag and tmo_new_flag:
            #             tmo_new = tmo_upg = tmo_price
            #         elif tmo_new_flag and not tmo_upg_flag:
            #             tmo_new = tmo_price
            #         else:
            #             tmo_upg = tmo_price

            dict_keys = ['ATT_new_price', 'ATT_upg_price',
                         'SPR_new_price', 'SPR_upg_price',
                         'VZW_new_price', 'VZW_upg_price',
                         'TMO_new_price', 'TMO_upg_price',
                         'Unactivated_price'
                         ]
            dict_values = [att_new, att_upg, spr_new, spr_upg, vzw_new, vzw_upg, tmo_new, tmo_upg, unactivated]
            activation_price_dict = dict(zip(dict_keys, dict_values))
            print(activation_price_dict)

        except Exception as e:
            print(f"An exception occurred: {e}")
            driver.quit()
            return None

        return activation_price_dict
