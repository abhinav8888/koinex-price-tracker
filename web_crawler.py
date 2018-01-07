#!/usr/bin/python
from __future__ import print_function
import os, sys, logging
import time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import settings


chrome_driver_path = '/Users/abhinav/Downloads/chromedriver' # path to the chromedriver
os.environ["webdriver.chrome.driver"] = chrome_driver_path

class Crawler(object):

    def __init__(self):
        self.driver = webdriver.Chrome(chrome_driver_path)

    def get_price_dict(self):
        self.driver.get('https://koinex.in')
        ticker_class = WebDriverWait(self.driver, 300).until(
        EC.presence_of_element_located((By.CLASS_NAME, "ticker-container")))
        price_tickers = ticker_class.find_elements_by_class_name('coin')
        price_data = [ticker.text for ticker in price_tickers]
        cleaned_price_data = self.clean_data(price_data)
        return cleaned_price_data

    def clean_data(self, price_data):
        data = dict()
        required_coin_abbr = ['BTC', 'XRP', 'LTC', 'ETH', 'BCH']
        for price_string in price_data:
            coin_name, price = price_string.split(': ')
            price = float(price.replace(',', ''))
            coin_name = coin_name.split('/')[0]
            if coin_name in required_coin_abbr:
                data[coin_name] = price
        # print(data)
        return data

    def play_youtube_video(self, url=settings.ALARM_YOUTUBE_URL):
        self.driver.get(url)
        time.sleep(60)
        self.driver.close()
