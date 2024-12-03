import os
import time
import logging
import threading
import requests
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import pwnagotchi.plugins as plugins
from pwnagotchi.ui.hw.libs.i2coled.oled import OLED

class OLEDBTCPrice(plugins.Plugin):
    __author__ = 'https://github.com/LOCOSP'
    __version__ = '1.0.0'
    __license__ = 'GPL3'
    __description__ = 'Displays cryptocurrency prices from Binance on OLED screens'
    
    __defaults__ = {
        'enabled': False,
        'pairs': ['BTCUSDT', 'ETHUSDT'],
        'update_interval': 300,
        'display_interval': 15,
    }

    def __init__(self):
        self.WIDTH = 128
        self.HEIGHT = 64
        self.running = True
        self.current_pair_index = 0
        self.prices = {}
        self.last_prices = {}
        self.last_price_update = 0
        self.last_display_update = 0

        self.plugin_dir = os.path.dirname(os.path.realpath(__file__))
        self.font = ImageFont.truetype(f'{self.plugin_dir}/OLEDstats/CyborgPunk.ttf', 24)
        self.price_font = ImageFont.truetype(f'{self.plugin_dir}/OLEDstats/CyborgPunk.ttf', 14)
        self.arrow_font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 20)

        self.oled_left = OLED(address=0x3C, width=self.WIDTH, height=self.HEIGHT)
        self.oled_left.Init()
        self.oled_left.Clear()
        
        self.oled_right = OLED(address=0x3D, width=self.WIDTH, height=self.HEIGHT)
        self.oled_right.Init()
        self.oled_right.Clear()

    def on_loaded(self):
        logging.info("OLED-CryptoStats plugin loaded")
        self.update_thread = threading.Thread(target=self._price_update_loop)
        self.update_thread.daemon = True
        self.update_thread.start()

    def _fetch_prices(self):
        try:
            pairs = self.options.get('pairs', self.__defaults__['pairs'])
            for pair in pairs:
                response = requests.get(f'https://api.binance.com/api/v3/ticker/price?symbol={pair}')
                if response.status_code == 200:
                    data = response.json()
                    current_price = float(data['price'])
                    if pair in self.prices:
                        self.last_prices[pair] = self.prices[pair]
                    self.prices[pair] = current_price
                    logging.info(f"Updated {pair} price: {current_price}")
        except Exception as e:
            logging.error(f"Failed to fetch prices: {e}")

    def _price_update_loop(self):
        while self.running:
            current_time = time.time()
            if current_time - self.last_price_update >= self.options.get('update_interval', self.__defaults__['update_interval']):
                self._fetch_prices()
                self.last_price_update = current_time
            time.sleep(1)

    def on_ui_update(self, ui):
        if not self.prices or not self.running:
            return

        current_time = time.time()
        if current_time - self.last_display_update >= self.options.get('display_interval', self.__defaults__['display_interval']):
            pairs = self.options.get('pairs', self.__defaults__['pairs'])
            self.current_pair_index = (self.current_pair_index + 1) % len(pairs)
            self.last_display_update = current_time

        current_pair = pairs[self.current_pair_index]
        current_price = self.prices.get(current_pair)
        last_price = self.last_prices.get(current_pair)
        
        symbol = current_pair[:3]
        arrow = "↑" if last_price and current_price > last_price else "↓"
        price_str = f"${current_price:.2f}"

        image_left = Image.new('1', (self.WIDTH, self.HEIGHT))
        draw_left = ImageDraw.Draw(image_left)
        image_right = Image.new('1', (self.WIDTH, self.HEIGHT))
        draw_right = ImageDraw.Draw(image_right)

        draw_left.text((0, 0), symbol, font=self.font, fill=255)
        draw_left.text((75, 0), arrow, font=self.arrow_font, fill=255)
        draw_left.text((0, 40), price_str, font=self.price_font, fill=255)

        if len(pairs) > 1:
            next_pair_index = (self.current_pair_index + 1) % len(pairs)
            next_pair = pairs[next_pair_index]
            next_price = self.prices.get(next_pair)
            next_symbol = next_pair[:3]
            next_arrow = "↑" if next_price and self.last_prices.get(next_pair) and next_price > self.last_prices[next_pair] else "↓"
            next_price_str = f"${next_price:.2f}" if next_price else "N/A"

            draw_right.text((0, 0), next_symbol, font=self.font, fill=255)
            draw_right.text((75, 0), next_arrow, font=self.arrow_font, fill=255)
            draw_right.text((0, 40), next_price_str, font=self.price_font, fill=255)

        self.oled_left.display(image_left)
        self.oled_right.display(image_right)


    def on_unload(self, ui):
        self.running = False
        if hasattr(self, 'update_thread'):
            self.update_thread.join()

        try:
            image_clear = Image.new('1', (self.WIDTH, self.HEIGHT))
            self.oled_left.display(image_clear)
            self.oled_right.display(image_clear)
        except Exception as e:
            logging.error(f"Error clearing displays: {e}")
        logging.info("OLED-CryptoStats plugin unloaded")
        