#!/usr/bin/env python

# DHT.py
# 2019-11-07
# Public Domain

import time
import logging

from pybattery.device_drivers.dht.models import (
    DhtModel,
    DhtStatus,
    PiProtocol,
)

import pigpio

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class DhtSensor:
    """
    A class to read the DHTXX temperature/humidity sensors.
    """

    def __init__(self, gpio: int, model: DhtModel, pi: PiProtocol | None = None):
        """
        Instantiate with the Pi and the GPIO connected to the
        DHT temperature and humidity sensor.

        Optionally the model of DHT may be specified.  It may be one
        of DHT11, DHTXX, or DHTAUTO.  It defaults to DHTAUTO in which
        case the model of DHT is automtically determined.

        The timestamp will be the number of seconds since the epoch
        (start of 1970).

        The status will be one of:
        0 DHT_GOOD (a good reading)
        1 DHT_BAD_CHECKSUM (receieved data failed checksum check)
        2 DHT_BAD_DATA (data receieved had one or more invalid values)
        3 DHT_TIMEOUT (no response from sensor)
        """
        pi = pi or pigpio.pi()

        self._pi = pi
        self._gpio = gpio
        self._model = model

        self._new_data = False
        self._in_code = False

        self._bits = 0
        self._code = 0

        self._status = DhtStatus.DHT_TIMEOUT
        self._timestamp = time.time()
        self._temperature = 0.0
        self._humidity = 0.0

        pi.set_mode(gpio, pigpio.INPUT)
        self._last_edge_tick = pi.get_current_tick() - 10000
        self._cb_id = pi.callback(gpio, pigpio.RISING_EDGE, self._rising_edge)

    def _datum(self) -> tuple[float, int, DhtStatus, float, float]:
        return (
            self._timestamp,
            self._gpio,
            self._status,
            self._temperature,
            self._humidity,
        )

    def _validate_DHT11(self, b1, b2, b3, b4):
        t = b2 + (b1 / 10.0)  # Include decimal part
        h = b4 + (b3 / 10.0)  # Include decimal part
        if (t >= 0) and (t <= 60) and (h >= 9) and (h <= 100):
            valid = True
        else:
            valid = False
        return (valid, t, h)

    def _validate_DHTXX(self, b1, b2, b3, b4):
        if b2 & 128:
            div = -10.0
        else:
            div = 10.0
        t = float(((b2 & 127) << 8) | b1) / div
        h = float((b4 << 8) | b3) / 10.0
        if (h <= 110.0) and (t >= -50.0) and (t <= 135.0):
            valid = True
        else:
            valid = False
        return (valid, t, h)

    def _decode_dhtxx(self):
        """
              +-------+-------+
              | DHT11 | DHTXX |
              +-------+-------+
        Temp C| 0-50  |-40-125|
              +-------+-------+
        RH%   | 20-80 | 0-100 |
              +-------+-------+

                 0      1      2      3      4
              +------+------+------+------+------+
        DHT11 |check-| dec  | temp | dec  | RH%  |
              |sum   |      |      |      |      |
              +------+------+------+------+------+
        DHT21 |check-| temp | temp | RH%  | RH%  |
        DHT22 |sum   | LSB  | MSB  | LSB  | MSB  |
        DHT33 |      |      |      |      |      |
        DHT44 |      |      |      |      |      |
              +------+------+------+------+------+
        """
        b0 = self._code & 0xFF
        b1 = (self._code >> 8) & 0xFF
        b2 = (self._code >> 16) & 0xFF
        b3 = (self._code >> 24) & 0xFF
        b4 = (self._code >> 32) & 0xFF

        chksum = (b1 + b2 + b3 + b4) & 0xFF

        if chksum == b0:
            if self._model == DhtModel.DHT11:
                valid, t, h = self._validate_DHT11(b1, b2, b3, b4)
            elif self._model == DhtModel.DHTXX:
                valid, t, h = self._validate_DHTXX(b1, b2, b3, b4)
            else:
                raise ValueError(f"Invalid DHT model: {self._model}")
            if valid:
                self._temperature = t
                self._humidity = h
                self._status = DhtStatus.DHT_GOOD
            else:
                self._status = DhtStatus.DHT_BAD_DATA
        else:
            self._status = DhtStatus.DHT_BAD_CHECKSUM
        self._new_data = True

    def _rising_edge(self, gpio, level, tick):
        edge_len = pigpio.tickDiff(self._last_edge_tick, tick)
        logger.debug(f"Rising edge: {(gpio, level, tick, edge_len)}")
        self._last_edge_tick = tick
        if edge_len > 10000:
            self._in_code = True  # We're now in a frame
            self._bits = (
                -1  # Ignore start sequence (-1: low, 0: high, 1: first bit, etc)
            )
            self._code = 0  # Initial code value
        elif self._in_code:
            self._bits += 1
            if self._bits >= 1:
                # Move previous bit up
                self._code <<= 1

                # Valid bit if 60–150 µs between rising edges
                if (edge_len >= 60) and (edge_len <= 150):
                    if edge_len > 100:
                        # 1 bit if edge_len > 0 otherwise it stays a 0 bit
                        self._code += 1
                else:
                    # invalid bit, end the frame
                    self._in_code = False
            if self._in_code:
                if self._bits == 40:
                    # We're still processing a frame and collected all 40 bits
                    self._decode_dhtxx()
                    self._in_code = False

    def _trigger(self):
        self._new_data = False
        self._timestamp = time.time()
        self._status = DhtStatus.DHT_TIMEOUT
        self._pi.write(self._gpio, 0)
        if self._model != DhtModel.DHTXX:
            time.sleep(0.018)
        else:
            time.sleep(0.001)
        self._pi.set_mode(self._gpio, pigpio.INPUT)

    def cancel(self):
        """ """
        if self._cb_id is not None:
            self._cb_id.cancel()
            self._cb_id = None

    def read(self) -> tuple[float, int, DhtStatus, float, float]:
        """
        This triggers a read of the sensor.

        The returned data is a tuple of timestamp, GPIO, status,
        temperature, and humidity.

        The timestamp will be the number of seconds since the epoch
        (start of 1970).

        The status will be one of:
        0 DHT_GOOD (a good reading)
        1 DHT_BAD_CHECKSUM (receieved data failed checksum check)
        2 DHT_BAD_DATA (data receieved had one or more invalid values)
        3 DHT_TIMEOUT (no response from sensor)
        """
        self._trigger()
        for _ in range(5):  # timeout after 0.25 seconds.
            time.sleep(0.05)
            if self._new_data:
                break
        datum = self._datum()
        return datum


# if __name__ == "__main__":
#     import sys
#     import pigpio
#     from pybattery.device_drivers.dht.dht_pigpio import DhtSensor

#     def callback(data):
#         print(
#             "{:.3f} {:2d} {} {:3.1f} {:3.1f} *".format(
#                 data[0], data[1], data[2], data[3], data[4]
#             )
#         )

#     argc = len(sys.argv)  # get number of command line arguments

#     if argc < 2:
#         print("Need to specify at least one GPIO")
#         exit()

#     pi = pigpio.pi()
#     if not pi.connected:
#         exit()

#     # Instantiate a class for each GPIO
#     # for testing use a GPIO+100 to mean use the callback
#     S = []
#     for i in range(1, argc):  # ignore first argument which is command name
#         g = int(sys.argv[i])
#         if g >= 100:
#             s = DhtSensor(pi, g - 100)
#         else:
#             s = DhtSensor(pi, g)
#         S.append((g, s))  # store GPIO and class

#     while True:
#         try:
#             for s in S:
#                 if s[0] >= 100:
#                     s[1].read()  # values displayed by callback
#                 else:
#                     d = s[1].read()
#                     print(
#                         "{:.3f} {:2d} {} {:3.1f} {:3.1f}".format(
#                             d[0], d[1], d[2], d[3], d[4]
#                         )
#                     )
#             time.sleep(2)
#         except KeyboardInterrupt:
#             break

#     for s in S:
#         s[1].cancel()
#         print("cancelling {}".format(s[0]))
#     pi.stop()
