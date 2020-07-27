import csv
from Scraper import Scraper
from Scraper import function_timer
from bs4 import BeautifulSoup
from regex import regex
from selenium.webdriver.support.ui import WebDriverWait


class CarrierScraper(Scraper):

    def __init__(self):
        super().__init__()
        self.scraper = Scraper()
        self.contents = self._get_contents()

    ####################################################################################################################
    # Functions for carrier phone pages                                                                                #
    ####################################################################################################################

    