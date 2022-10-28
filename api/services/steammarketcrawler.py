import requests

BUY_ORDER = "highest_buy_order"
SELL_ORDER = "lowest_sell_order"
KEY_FOR_ID = "Market_LoadOrderSpread"
ITEM_URL_TEMPLATE_URL = "https://steamcommunity.com/market/itemordershistogram?country=DE&language=german&currency=1&two_factor=0"


class SteamMarketCrawler:
    """Gets prices from the steam market, given a url"""

    @staticmethod
    def _getPricesFromUrl(url: str) -> dict:
        raw_code = requests.get(url).text

        splits = raw_code.split(",")

        d = {}

        for split in splits:
            s = split.split(":")
            if len(s) == 2:
                k, v = s
                k = k.replace("\"", "")
                v = v.replace("\"", "")

                if k.lower() in [BUY_ORDER, SELL_ORDER]:
                    d[k] = int(v) / 100
        return d

    @classmethod
    def pricesFromMarketURL(cls, url: str) -> dict:
        """
        Gets the prices from a steam market url.

        :returns dict: A dict with the keys "lowest_sell_order" and "highest_buy_order"

        """
        try:
            raw_code = requests.get(url).text

            splitted = raw_code.split(",")

            pos = raw_code.index(KEY_FOR_ID)
        except Exception:
            raise ValueError("invalid URL")


        is_num = False
        id_ = ""
        data = {}
        while not len(id_) or is_num:
            pos += 1

            char = raw_code[pos]

            try:

                id_ += str(int(char))
                is_num = True
            except Exception:
                is_num = False

        print(id_)

        try:
            item_id = int(id_)
            data = cls._getPricesFromUrl(f"{ITEM_URL_TEMPLATE_URL}&item_nameid={item_id}")
            # print(data)
        except Exception:
            print("couldnt convert id")
        return data
