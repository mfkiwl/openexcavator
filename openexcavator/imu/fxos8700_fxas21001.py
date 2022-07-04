import threading
import time
import board
from adafruit_fxos8700 import FXOS8700
from adafruit_fxas21002c import FXAS21002C
from imu.lib.fusion import Fusion


class FXOS8700_FXAS21002C(threading.Thread):

    def __init__(self, i2c=None):
        """
        :param i2c: I2C bus, will be created if not supplied.
        """
        super().__init__()
        # TODO: add try/except block for notifying the user when the IMU is not/incorrectly connected
        # start I2C driver and initialize FXOS8700 and FXAS21002C
        if not i2c:
            i2c = board.I2C()
        self.__fxos = FXOS8700(i2c)
        self.__fxas = FXAS21002C(i2c)
        self.__fuse = Fusion(timediff=lambda ts, start_time: ts - start_time)

    def read_all(self):
        """
        Read all the raw sensor values at once.  
        :returns: accelerometer(x,y,z), gyroscope(x,y,z), magnetometer(x,y,z)
        """
        return self.read_accelerometer(), self.read_gyroscope(), self.read_magnetometer(), time.time()

    def read_accelerometer(self):
        """
        Read the raw accelerometer value.
        :returns: accelerometer x,y,z
        """
        return self.__fxos.accelerometer

    def read_magnetometer(self):
        """
        Read the raw magnetometer value.
        :returns: magnetometer x,y,z
        """
        return self.__fxos.magnetometer

    def read_gyroscope(self):
        """
        Read the raw gyroscope value.
        :returns: gyroscope x,y,z
        """
        return self.__fxas.gyroscope

    def run(self):
        """
        Start the fusion model updating loop.
        """
        while True:
            self.__fuse.update(*self.read_all())
            time.sleep(0) # Allow other threads to access i2c bus.

    def get_data(self):
        """
        Parse the IMU data after fusion applied.
        :returns: dict with: roll, pitch, yaw, imu_time.
        """
        return {"roll": self.__fuse.roll,
                "pitch": self.__fuse.pitch,
                "yaw": self.__fuse.heading,
                "imu_time": self.__fuse.deltat.start_time}

def test_loop():
    imu = FXOS8700_FXAS21002C()
    imu.start()
    time.sleep(1)
    while True:
        print("----------------------------------------------------")
        print('Acceleration (m/s^2): ({0:0.3f},{1:0.3f},{2:0.3f})'.format(*imu.read_accelerometer()))
        print('Magnetometer (uTesla): ({0:0.3f},{1:0.3f},{2:0.3f})'.format(*imu.read_magnetometer()))
        print('Gyroscope (radians/s): ({0:0.3f},{1:0.3f},{2:0.3f})'.format(*imu.read_magnetometer()))

        print('Roll: {0}, pitch: {1}, heading: {2}, Time: {3}'.format(*imu.parse_data()))
        time.sleep(0.5)
