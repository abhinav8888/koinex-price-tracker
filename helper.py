import redis, json, urllib
from datetime import datetime, timedelta
from ast import literal_eval
import settings
import requests

class Helper(object):

    def __init__(self, **kwargs):
        self.redis_conn = None

    def get_redis_connection(self):
        """
        Establishes a redis connection and sets attribute to be used for that thread
        :return: 
        """
        if getattr(self, 'redis_conn', None):
            return self.redis_conn
        redis_conn = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)
        self.redis_conn = redis_conn
        return redis_conn

    def set_max_min_price_for_coin(self, coin_symbol, max_price=0, min_price=0):
        redis_conn = self.get_redis_connection()
        price_dict = dict()
        if max_price:
            price_dict['max'] = max_price
        if min_price:
            price_dict['min'] = min_price
        if price_dict:
            redis_conn.hmset(coin_symbol, price_dict)

    def get_price_alerts_for_coin(self, coin_symbol):
        redis_conn = self.get_redis_connection()
        price_dict = redis_conn.hgetall(coin_symbol)
        return price_dict

    def get_price_history(self):
        redis_conn = self.get_redis_connection()
        now = datetime.now()
        key = '_koinex_data_%s' % now.date()
        price_history = redis_conn.hgetall(key)
        return price_history

    def get_koinex_price(self):
        koinex_api_url =  'https://koinex.in/api/ticker'
        all_data = requests.get(koinex_api_url).json() #json.loads(urllib.urlopen(koinex_api_url).read())
        price_data = Helper.clean_data(all_data['prices']['inr'])
        self.koinex_prices = price_data
        return price_data

    def get_zebpay_prices(self):
        zebpay_api_url = 'https://live.zebapi.com/api/v1/ticker?currencyCode=inr'
        resp = requests.get(zebpay_api_url)
        if resp.status_code == 200:
            prices = resp.json()
            self.zebpay_prices = prices
            return prices

    def save_price_data_in_redis(self, price_data):
        redis_conn = self.get_redis_connection()
        selling_suggested, buying_suggested = [], []
        now = datetime.now()
        key = '_koinex_data_%s'
        redis_conn.hmset(key % now.date(), {now: price_data})
        redis_conn.delete(key % (now - timedelta(days=7)).date())
        for coin, price in price_data.items():
            coin_price_dict = redis_conn.hgetall(coin)
            if float(coin_price_dict.get('max', 0)) < price:
                self.set_max_min_price_for_coin(coin, max_price=price)
                selling_suggested.append({'coin': coin, 'price': price})
            if not coin_price_dict.get('min') or float(coin_price_dict.get('min')) > price:
                self.set_max_min_price_for_coin(coin, min_price=price)
                buying_suggested.append({'coin': coin, 'price': price})
        return {'buy_coins': buying_suggested, 'sell_coins':selling_suggested} if buying_suggested or selling_suggested else None

    @staticmethod
    def clean_data(price_data):
        valid_coin_abbreviations = settings.VALID_COINS
        data = {coin:float(price) for coin, price in price_data.items() if coin in valid_coin_abbreviations}
        return data

    def get_coin_price_history(self, coin):
        data = self.get_price_history()
        for timestamp in sorted(data.keys()):
            print(timestamp, literal_eval(data[timestamp])[coin])

    def koinex_alert(self, ltc_price):
        return ltc_price < 21000 or ltc_price > 24000


    def send_slack_alert(self, coin_name, price, exchange='koinex'):
        msg = '%s - %s - %s' % (coin_name, price, exchange)
        payload = json.dumps({'text': msg})
        requests.post(settings.SLACK_URL, data=payload)

    def update_price_alerts(self, price_alerts):
        for alert in price_alerts:
            self.set_max_min_price_for_coin(alert[0], float(alert[1]), float(alert[2]))

    def check_zebpay_koinex_arbitrage(self):
        koinex_prices = getattr(self, 'koinex_prices', None)
        if not koinex_prices:
            koinex_prices = self.get_koinex_price()
        zebpay_prices = getattr(self, 'zebpay_prices', None)
        if not zebpay_prices:
            zebpay_prices = self.get_zebpay_prices()
        invested_amount = 20000
        gateway_charges = 0.02
        transfer_charges = 0.0005
        tranfer_charge = transfer_charges * zebpay_prices['buy']
        selling_amount = (invested_amount*(1-gateway_charges)*koinex_prices['BTC'])/zebpay_prices['buy']
        
        return selling_amount

    def check_trx_price(self):
        url = 'https://api.binance.com/api/v3/ticker/price?symbol=TRXETH'
        resp = requests.get(url)
        if resp.status_code == 200:
            data = resp.json()
            price = float(data['price'])
            if price < 0.00009 or price > 0.00015:
                self.send_slack_alert('TRX', data['price'], 'Binance')

    def check_ada_price(self):
        url = 'https://api.binance.com/api/v3/ticker/price?symbol=ADAETH'
        resp = requests.get(url)
        if resp.status_code == 200:
            data = resp.json()
            price = float(data['price'])
            if price < 0.00053542  or price > 0.0007:
                self.send_slack_alert('ADA', data['price'], 'Binance')


    def check_poe_price(self):
        url = 'https://api.binance.com/api/v3/ticker/price?symbol=POEETH'
        resp = requests.get(url)
        if resp.status_code == 200:
            data = resp.json()
            price = float(data['price'])
            if price < 0.00009  or price > 0.00015:
                self.send_slack_alert('POE', data['price'], 'Binance')

    def check_coin_price_on_binance(self, coin, market='ETH'):
        url = 'https://api.binance.com/api/v3/ticker/price?symbol=%s%s' % (coin, market)
        resp = requests.get(url)
        if resp.status_code == 200:
            data = resp.json()
            return data
