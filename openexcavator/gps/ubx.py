from collections import deque
import datetime
from queue import Queue
import threading
import time
import serial
from pyubx2 import UBXReader


class UBX(threading.Thread):
    def __init__(
        self,
        gps_queue: deque,
        serial_port="/dev/ttyACM0",
        baud_rate=115200,
        ntrip_queue: Queue = None,
    ):
        """
        Initialize the UBX receiver module.
        :param serial_port: the serial port the UBX receiver is connected to.
        :param baud_rate: the baud rate to use.
        """
        super().__init__(daemon=True)
        self._gps_queue = gps_queue
        self._serial = serial.Serial(port=serial_port, baudrate=baud_rate, timeout=0.1)
        self._ubr = UBXReader(self._serial, protfilter=1)
        self.ntrip_queue = ntrip_queue

    def run(self):
        """
        Start the read nmea messages from serial loop.
        """
        self.running = True
        data = {}
        while self.running:
            # Writes data to ntrip server if available in queue.
            self.write_ntrip()

            # Parse data from UBX receiver.
            (raw_data, parsed_data) = self._ubr.read()
            if parsed_data is None:
                continue

            if parsed_data.msgID == "GGA":  # GPS Fix Data
                data["lat"] = parsed_data.lat
                data["lng"] = parsed_data.lon
                data["alt"] = parsed_data.alt
                data["fix"] = parsed_data.quality
            elif parsed_data.msgID == "GST":  # Estimated error in position solution
                data["acc"] = max(parsed_data.stdLat, parsed_data.stdLong)
            elif parsed_data.msgID == "ZDA":  # ZDA Time
                data["ts"] = datetime.datetime.combine(
                    datetime.date(parsed_data.year, parsed_data.month, parsed_data.day),
                    parsed_data.time,
                )
            elif parsed_data.msgID == "UBX" and parsed_data.msgId == "00":  # GPS Acc Data
                data["speed"] = parsed_data.SOG
                data["track"] = parsed_data.COG
                data["pdop"] = parsed_data.PDOP
                data["hdop"] = parsed_data.HDOP
                data["vdop"] = parsed_data.VDOP
                data["hacc"] = parsed_data.hAcc
                data["vacc"] = parsed_data.vAcc
            self._gps_queue.append(data)

    def write_ntrip(self):
        """
        Write data to ntrip server if available in queue.
        """
        if self.ntrip_queue and not self.ntrip_queue.empty():
            (raw_data, parsed_data) = self.ntrip_queue.get()
            self._serial.write(raw_data)
            self.ntrip_queue.task_done()

    def stop(self):
        """Set property to stop thread"""
        self.running = False


def test_loop():
    queue = deque(maxlen=1)
    imu = UBX(queue)
    imu.start()
    time.sleep(1)
    while True:
        data: dict = queue[-1]
        if len(data) == 5:
            print(f'lat: {data["lat"]}, long: {data["lng"]}, alt: {data["alt"]}, acc: {data["acc"]}, fix: {data["fix"]}')
        time.sleep(0.5)
