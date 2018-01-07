import os, sys
import argparse
import settings
from helper import Helper

parser = argparse.ArgumentParser(description='Set max and minimum price of coins for alerts')

parser.add_argument('--coin',
    help='Abbreviation of the coin used in exchanges. Valid abbreviations are %s' % settings.VALID_COINS)
parser.add_argument('--max_price',
    help='Max price of the coin')
parser.add_argument('--min_price',
    help='Min price of the coin')

args = parser.parse_args()

def main():
    helper = Helper()
    coin_abbrv = args.coin
    try:
        max_price = int(args.max_price)
    except (TypeError, ValueError):
        print "Enter max price in correct format"
        max_price = None
    try:
        min_price = int(args.min_price)
    except (TypeError, ValueError):
        print "Enter min price in correct format"
        min_price = None
    if coin_abbrv and (max_price or min_price):
        helper.set_max_min_price_for_coin(coin_symbol=args.coin, max_price=max_price, min_price=min_price)


if __name__ == '__main__':
    main()
