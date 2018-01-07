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
        redis_conn = redis.StrictRedis(host='localhost', port=6379, db=0)
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
        price_data = Helper.clean_data(all_data['prices'])
        return price_data

    def save_price_data_in_redis(self, price_data):
        redis_conn = self.get_redis_connection()
        selling_suggested, buying_suggested = [], []
        now = datetime.now()
        key = '_koinex_data_%s'
        redis_conn.hmset(key % now.date(), {now: price_data})
        redis_conn.delete(key % (now - timedelta(days=7)).date())
        for coin, price in price_data.iteritems():
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
        data = {coin:float(price) for coin, price in price_data.iteritems() if coin in valid_coin_abbreviations}
        return data

    def get_coin_price_history(self, coin):
        data = self.get_price_history()
        for timestamp in sorted(data.keys()):
            print timestamp, literal_eval(data[timestamp])[coin]

    def koinex_alert(self, ltc_price):
        return ltc_price < 21000 or ltc_price > 24000


    def send_slack_alert(self, coin_name, price):
        msg = 'Price of %s on koinex is %s' % (coin_name, price)
        payload = json.dumps({'text': msg})
        requests.post(settings.SLACK_URL, data=payload)
