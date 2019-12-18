# -*- coding: utf-8 -*-

import RPi.GPIO as GPIO
import time
import threading
import json

from . utils import BidirectionalMultiDict


class HX711(threading.Thread):
    gain_bits_map = BidirectionalMultiDict(((128, 25), (64, 27), (32, 26)))

    def __init__(
                self, dout, pd_sck, gain, offset=0.0, reference_unit=1.0,
                hook=None
            ):
        super(HX711, self).__init__()
        self.__dout = dout
        self.__pd_sck = pd_sck
        self.__gain = self.gain_bits_map[gain]
        self.__offset = offset
        self.__reference_unit = reference_unit
        self.__latest_value = 0.0
        self.__hook = hook if hook is not None else lambda v: None
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.__pd_sck, GPIO.OUT)
        GPIO.setup(self.__dout, GPIO.IN)
        self.reset()
        self.__renew()

    @property
    def reference_unit(self):
        return self.__reference_unit

    @reference_unit.setter
    def reference_unit(self, val):
        self.__reference_unit = float(val)

    @property
    def offset(self):
        return self.__offset

    @offset.setter
    def offset(self, val):
        self.__offset = float(val)

    def get_raw_value(self):
        while not self.is_ready():
            time.sleep(0.0001)
        res = 0
        for _ in range(24):
            GPIO.output(self.__pd_sck, True)
            res <<= 1
            GPIO.output(self.__pd_sck, False)
            if GPIO.input(self.__dout):
                res += 1
        for i in range(self.__gain - 24):
            GPIO.output(self.__pd_sck, True)
            GPIO.output(self.__pd_sck, False)
            GPIO.input(self.__dout)
        return -(res & 0x800000) + (res & 0x7fffff)

    def export_parameters(self, f):
        if hasattr(f, 'write') and callable(f.write):
            return json.dump({
                'offset': self.__offset,
                'reference_unit': self.__reference_unit
            }, f)
        if isinstance(f, str):
            with open(f, 'w') as fout:
                return self.export_parameters(fout)
        raise ValueError(type(f))

    def import_parameters(self, f):
        if hasattr(f, 'read') and callable(f.read):
            obj = json.load(f)
            if 'offset' in obj:
                self.__offset = obj['offset']
            if 'reference_unit' in obj:
                self.__reference_unit = obj['reference_unit']
            return self
        if isinstance(f, str):
            with open(f) as fin:
                return self.import_parameters(fin)
        raise ValueError(type(f))

    def is_ready(self):
        return GPIO.input(self.__dout) == 0

    def attributes(self):
        return ('weight', 'raw_value')

    def values(self):
        return (self.weight, self.raw_value)

    @property
    def raw_value(self):
        return self.__last_value

    @property
    def weight(self):
        return (self.raw_value * self.__reference_unit) + self.__offset

    def __getitem__(self, attr):
        if attr in self.attributes():
            return getattr(self, attr)
        raise KeyError(attr)

    def set_offset(self, offset):
        self.__offset = offset

    def set_reference_unit(self, reference_unit):
        self.__reference_unit = reference_unit

    def tare(self):
        self.set_offset(self.weight)

    def get_median3(self):
        buf = sorted(self.get_raw_value() for i in range(3))
        return buf[1]

    def power_down(self):
        GPIO.output(self.__pd_sck, False)
        GPIO.output(self.__pd_sck, True)
        time.sleep(0.0001)

    def power_up(self):
        GPIO.output(self.__pd_sck, False)
        time.sleep(0.0001)

    def reset(self):
        self.power_down()
        self.power_up()

    def __renew(self):
        self.__last_value = self.get_median3()

    def run(self):
        self.reset()
        while not self.is_ready():
            time.sleep(0.0001)
        while True:
            self.__renew()
            self.__hook(dict(zip(self.attributes(), self.values())))
            self.reset()
            time.sleep(0.2)
