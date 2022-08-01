from collections import deque
import datetime
import logging
import threading
import time
import board
from adafruit_fxos8700 import FXOS8700
from adafruit_fxas21002c import FXAS21002C

import ahrs
from ahrs.filters import Madgwick as Filter
import numpy as np

# Accelerometer correction values
ACC_MULTIPLIER = np.array([0.10337778, 0.10565876, 0.10290373])
ACC_ADD = np.array([-0.02782111, 0.05567155, -0.02035833])

# Gyroscope correction values
GYR_SUB = np.array([0.013372903624167489, 0.0024461880297483025, 0.006094335227959888])

# Magnetometer correction values
MAG_SUB = np.array([-26.7, -29.35, -88.2])


class FXOS8700_FXAS21002C(threading.Thread):
    def __init__(self, i2c=None):
        """
        :param i2c: I2C bus, will be created if not supplied.
        """
        super().__init__(daemon=True)
        # TODO: add try/except block for notifying the user when the IMU is not/incorrectly connected
        # start I2C driver and initialize FXOS8700 and FXAS21002C
        if not i2c:
            i2c = board.I2C()
        self._fxos = FXOS8700(i2c)
        self._fxas = FXAS21002C(i2c)
        self._imu_time = None
        self._data_queue = deque(maxlen=1)

    def read_all(self):
        """
        Read all the raw sensor values at once.
        :returns: gyroscope(x,y,z), accelerometer(x,y,z), magnetometer(x,y,z)
        """
        return self.read_gyroscope(), self.read_accelerometer(), self.read_magnetometer()

    def read_accelerometer(self):
        """
        Read the raw accelerometer value (m/s^2).
        :returns: accelerometer x,y,z
        """
        return np.add(np.multiply(np.asarray(self._fxos.accelerometer), ACC_MULTIPLIER), ACC_ADD)

    def read_magnetometer(self):
        """
        Read the raw magnetometer value (uTesla).
        :returns: magnetometer x,y,z
        """
        return np.subtract(np.asarray(self._fxos.magnetometer), MAG_SUB)

    def read_gyroscope(self):
        """
        Read the raw gyroscope value (radians/s).
        :returns: gyroscope x,y,z
        """
        return np.subtract(np.asarray(self._fxas.gyroscope), GYR_SUB)

    def run(self):
        """
        Start the fusion model updating loop.
        """
        self.running = True
        filter = Filter()
        q = ahrs.common.orientation.ecompass(
            self.read_accelerometer(),
            self.read_magnetometer(),
            frame="ENU",
            representation="quaternion",
        )
        while True:
            data = self.read_all()
            now = datetime.datetime.utcnow().timestamp()
            q = filter.updateMARG(q, *data, dt=now - self._imu_time if self._imu_time else None)
            self._imu_time = now
            self._data_queue.append(ahrs.common.orientation.q2rpy(q, in_deg=True))
            time.sleep(0.05)  # Allow other threads to access i2c bus.

    def get_data(self):
        """
        Parse the IMU data after fusion applied.
        :returns: dict with: roll, pitch, yaw, imu_time.
        """
        try:
            data = self._data_queue[-1]
            return {
                "roll": data[0],
                "pitch": data[1],
                "yaw": data[2],
                "imu_time": self._imu_time,
            }
        except IndexError:
            logging.error("No processed data available, make sure the IMU thread is started.")
            return {}

    def stop(self):
        """Set property to stop thread"""
        self.running = False


def test_loop():
    imu = FXOS8700_FXAS21002C()
    imu.start()
    time.sleep(1)
    while True:
        # print("----------------------------------------------------")
        # print('Acceleration (m/s^2): ({0:0.3f},{1:0.3f},{2:0.3f})'.format(*imu.read_accelerometer()))
        # print('Magnetometer (uTesla): ({0:0.3f},{1:0.3f},{2:0.3f})'.format(*imu.read_magnetometer()))
        # print('Gyroscope (radians/s): ({0:0.3f},{1:0.3f},{2:0.3f})'.format(*imu.read_gyroscope()))

        print("Roll: {0:0.3f}, pitch: {1:0.3f}, heading: {2:0.3f}, Time: {3:0.2f}".format(*imu.get_data().values()))
        time.sleep(0.5)
