#!/usr/bin/python
from __future__ import print_function
import os, sys, logging
import socket

ROOT_FOLDER = os.path.realpath(os.path.dirname(__file__))
ROOT_FOLDER = ROOT_FOLDER[:ROOT_FOLDER.rindex('/')]

if ROOT_FOLDER not in sys.path:
    sys.path.insert(1, ROOT_FOLDER + '/')

from web_crawler import Crawler
from update_google_sheets import UpdateSheet
from helper import Helper

log_file = 'koinex.log'
logging.basicConfig(filename=log_file,level=logging.ERROR)


def main():
    crawl = None
    try:
        helper = Helper()
        price_data = helper.get_koinex_price()
        sheet = UpdateSheet()
        sheet.update_koinex_google_sheet(price_data)
        if helper.koinex_alert(price_data['LTC']):
           helper.send_slack_alert(coin_name='LTC', price=price_data['LTC'])
        transaction_required = helper.save_price_data_in_redis(price_data)
        print(transaction_required)
        if transaction_required:
            for coin_data in transaction_required['buy_coins']:
                logging.error('%s' % coin_data)
                helper.send_slack_alert(coin_data['coin'], coin_data['price'])
            logging.error('Selling recommended for following coins')
            for coin_data in transaction_required['sell_coins']:
                helper.send_slack_alert(coin_data['coin'], coin_data['price'])
            # crawl = Crawler()
            # crawl.play_youtube_video()
    except Exception, e:
        logging.error(e)
        print(e)
    try:
        if crawl:
            crawl.driver.close()
    except:
        pass

if __name__ == '__main__':
    main()
