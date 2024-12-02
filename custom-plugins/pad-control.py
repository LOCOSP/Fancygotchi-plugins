import logging
import evdev
from evdev import InputDevice, ecodes
import subprocess
import pwnagotchi.plugins as plugins

class GamepadMenuControl(plugins.Plugin):
    __author__ = 'https://github.com/LOCOSP'
    __version__ = '0.1.0'
    __license__ = 'GPL3'
    __description__ = 'Plugin to control Fancygotchi 2.0 menu using a USB gamepad.'

    def __init__(self):
        self.device_path = '/dev/input/event0'
        self.device = None

    def runcommand(self, command):
        logging.info(f"Running command: {command}")
        subprocess.run(command, shell=True)

    def on_loaded(self):
        logging.info("Gamepad Menu Control plugin loaded.")
        self.device_path = self.options.get("device_path", self.device_path)

        try:
            self.device = InputDevice(self.device_path)
            logging.info(f"Gamepad connected: {self.device_path}")
        except FileNotFoundError:
            logging.error(f"Gamepad device not found at {self.device_path}")

    def on_unload(self, ui):
        logging.info("Gamepad Menu Control plugin unloaded.")

    def on_ready(self, ui):
        logging.info("Starting gamepad event loop.")
        if self.device:
            for event in self.device.read_loop():
                if event.type == ecodes.EV_ABS:
                    logging.info(f"Axis event: code {event.code}, value {event.value}")
                    if event.code == ecodes.ABS_Y:  # Up/Down
                        if event.value == 0:
                            self.runcommand("fancytools -m up")
                        elif event.value == 255:  # value 255 - down
                            self.runcommand("fancytools -m down")
                    elif event.code == ecodes.ABS_X:  # Left/Right
                        if event.value == 0:  # value 0 - w left
                            self.runcommand("fancytools -m left")
                        elif event.value == 255:  # value 255 - right
                            self.runcommand("fancytools -m right")

                elif event.type == ecodes.EV_KEY:  # buttons
                    logging.info(f"Button event: code {event.code}, value {event.value}")
                    if event.code == 289 and event.value == 1:  # button B pressed
                        self.runcommand("fancytools -m toggle")
                    elif event.code == 290 and event.value == 1:  # button A pressed
                        self.runcommand("fancytools -m select")