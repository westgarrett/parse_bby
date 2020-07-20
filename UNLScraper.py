import time

from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.action_chains import ActionChains
from Scraper import Scraper


class UNLScraper(Scraper):

    def __init__(self, url):
        super().__init__(url)
        self.contents = self._get_contents()

    ####################################################################################################################
    # Functions for unlocked phone pages                                                                               #
    ####################################################################################################################

    @staticmethod
    def find_carrier_price(page_content, company):
        return page_content.find("button", attrs={"data-track": f"{company}"}).parent.find_next("span").find_next(
            "span").text

    @staticmethod
    def find_disclaimer(page_content):
        return page_content.find("div", attrs={"class": "carriers-page__disclaimer"}).text

    @staticmethod
    def find_activation_type_button(page_content, activation_type):
        return page_content.find("button", attrs={"data-track": f"{activation_type}"})

    @staticmethod
    def contains_disclaimer(tag):
        if "Starting at" in tag:
            return True
        return False

    @staticmethod
    def find_disclaimer_price(disclaimer):
        disclaimer_dict = {}
        bstr = ""
        # Removes the carat value and the period at the end of the tag
        for ch in disclaimer[1:len(disclaimer) - 1]:
            if ch.isdigit() or ch == "$" or ch == "." or ch == ",":
                bstr += ch
        # Returns the build string as a list split on the comma, and removes the carat 1 at the beginning of the string
        bstr = bstr.split(",")
        return bstr

    @staticmethod
    def find_carrier_activation_button_selenium(company, driver):
        return driver.find_element_by_xpath(f'//*[@data-track="{company}"]')

    @staticmethod
    def find_carrier_continue_button_selenium(driver):
        return driver.find_element_by_xpath('//*[@data-track="continue"]')

    @staticmethod
    def find_no_trade_in_button_selenium(driver):
        return driver.find_element_by_xpath('//*[@data-track="trade-in-optin-no"]')

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
    def get_activation_prices(self, sku, driver):
        price_page = f"https://www.bestbuy.com/wireless/transaction-types/render/carriers?numberOfPayments=1&purchaseType=FULL_SRP&skuId={sku}"
        # Must use a Selenium driver because the pricing is the result of a javascript function
        driver.get(price_page)

        # Grabs the innerHTML generated by javascript
        html = driver.execute_script("return document.documentElement.innerHTML;")
        page_content = BeautifulSoup(html, "html5lib")

        # Make sure to quit out of the selenium driver after the script is through
        # if disclaimer is present, there is a different pricing for upg/new line
        vzw_upg = vzw_new = att_upg = att_new = spr_upg = spr_new = tmo_upg = tmo_new = unactivated = "-1"
        disclaimer = disclaimer_price = None
        try:
            try:
                disclaimer = self.find_disclaimer(page_content)
                disclaimer_price = self.find_disclaimer_price(disclaimer)
                print(f"Disclaimer pricing: {disclaimer_price}")
            except Exception:
                if disclaimer is None:
                    print(f"Disclaimer not present, presumably Upg == New for {sku}")

            try:
                vzw_price = self.find_carrier_price(page_content, "Verizon")
                verizon_element_present = True
            except Exception:
                verizon_element_present = False

            try:
                att_price = self.find_carrier_price(page_content, "ATT")
                att_element_present = True
            except Exception:
                att_element_present = False

            try:
                spr_price = self.find_carrier_price(page_content, "Sprint")
                spr_element_present = True
            except Exception:
                spr_element_present = False

            try:
                tmo_price = self.find_carrier_price(page_content, "TMobile")
                tmo_element_present = True
            except Exception:
                tmo_element_present = False

            try:
                unactivated = self.find_carrier_price(page_content, "activate-later")
                unactivated_element_present = True
            except Exception:
                unactivated_element_present = False

            # Verizon
            if verizon_element_present:
                if self.contains_disclaimer(vzw_price):
                    print("vzw has disclaimer")
                    vzw_new = disclaimer_price[0]
                    vzw_upg = disclaimer_price[1]
                # Check if allowing unlocked activations on new lines and upgrades. Not necessary if contains_disclaimer()
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
                if self.contains_disclaimer(att_price):
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
                if self.contains_disclaimer(spr_price):
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
            if tmo_element_present:
                if self.contains_disclaimer(tmo_price):
                    print("tmo has disclaimer")
                    tmo_new = disclaimer_price[0]
                    tmo_upg = disclaimer_price[1]
                else:
                    flag = self.line_activation_available(sku, "TMobile", driver)
                    tmo_upg_flag = flag[0]
                    tmo_new_flag = flag[1]
                    if tmo_upg_flag and tmo_new_flag:
                        tmo_new = tmo_upg = tmo_price
                    elif tmo_new_flag and not tmo_upg_flag:
                        tmo_new = tmo_price
                    else:
                        tmo_upg = tmo_price

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
            print("An exception occured")
            print(e)
            driver.quit()
            return None

        return activation_price_dict
