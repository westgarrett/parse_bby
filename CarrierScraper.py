from Scraper import Scraper

class CarrierScraper(Scraper):

    def __init__(self, url=""):
        super().__init__(url)
        self.contents = self._get_contents()

