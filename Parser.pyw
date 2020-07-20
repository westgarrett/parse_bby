import requests
from bs4 import BeautifulSoup
import time
import selenium
import html5lib
import validators
import regex
import threading
from validator_collection import checkers
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from regex import compile
import asyncio
import aiohttp


# This class looks for certain information each product page
class Parser:
    def __init__(self, page_content):
        self.content = page_content

