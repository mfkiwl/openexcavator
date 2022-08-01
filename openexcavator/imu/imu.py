from collections import deque
import logging
from typing import Callable


class IMUHandler:
    def __init__(self, config, i2c=None):
        self.threads = []
        self.__data_func = self._parse_data_func(config, i2c)

    def get_data(self):
        """
        Get the current IMU data.
        :returns: dict with: roll, pitch, yaw, imu_time.
        """
        return self.__data_func()

    def _parse_data_func(self, config, i2c) -> Callable:
        """
        Parse a IMU data function with no parameters and and return it.
        :returns: function that return dict with: roll, pitch, yaw, imu_time.
        """
        if config["imu_type"] == "Reach":
            from reach.imu import ReachIMU

            imu_queue = deque(maxlen=1)
            reach_imu = ReachIMU(config["imu_host"], int(config["imu_port"]), imu_queue)
            reach_imu.start()
            self.threads.append(reach_imu)
            return lambda: imu_queue[-1]

        if config["imu_type"] == "Simulator":
            # from simulator.imu import SimulatorIMU

            # sim_imu = SimulatorIMU(config["imu_host"], int(config["imu_port"]))
            # sim_imu.start()
            # self.threads.append(sim_imu)
            # return lambda: sim_imu.get_data()
            return NotImplementedError

        if config["imu_type"] == "FXOS8700+FXAS21001":
            from imu.fxos8700_fxas21001 import FXOS8700_FXAS21002C

            fxos8700_fxas21001_imu = FXOS8700_FXAS21002C(i2c)
            fxos8700_fxas21001_imu.start()
            self.threads.append(fxos8700_fxas21001_imu)
            return lambda: fxos8700_fxas21001_imu.get_data()

        return NotImplementedError

    def disconnect_source(self):
        for thread in self.threads:
            if hasattr(thread, "disconnect_source"):
                thread.disconnect_source()

    def stop(self):
        """Stop IMU threads if they are running."""
        if len(self.threads) == 0:
            return

        for thread in self.threads:
            thread.stop()
        self.threads = []
        logging.info("IMU threads stopped")
        return True
