import settings
from helper import Helper


def main():
    helper = Helper()
    coin_abbreviations = settings.VALID_COINS
    for coin_abbreviation in coin_abbreviations:
        price_alerts = helper.get_price_alerts_for_coin(coin_abbreviation)
        print('%s: max_price:%s, min_price:%s' % (coin_abbreviation, price_alerts['max'], price_alerts['min']))


if __name__ == '__main__':
    main()
