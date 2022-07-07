"""
Created on Oct 19, 2017

@author: ionut
"""

import sqlite3


def get_config():
    """Return dict of key-value from config table"""
    conn = sqlite3.connect("openexcavator.db")
    cursor = conn.cursor()
    cursor.execute("SELECT key,value FROM config")
    config = {}
    rows = cursor.fetchall()
    for row in rows:
        config[row[0]] = row[1]
    conn.close()
    return config


def set_config(data):
    """
    Store configuration using key-value pairs in config table
    :param data: dict of key-value pairs
    """
    conn = sqlite3.connect("openexcavator.db")
    cursor = conn.cursor()
    config = get_config()
    for key, value in config.items():
        if key not in data or data[key] is None:
            continue
        if str(value) != str(data[key]):
            cursor.execute("UPDATE config SET value=? WHERE key=?", (data[key], key))
            conn.commit()
    conn.close()


def create_structure():
    """Create database and config table if it does not exist"""
    conn = sqlite3.connect("openexcavator.db")
    cursor = conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS config(id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT, value TEXT,CONSTRAINT config_unique_key UNIQUE(key))""")
    conn.commit()
    conn.close()


def populate_config():
    """Populate configuration table with default values"""
    conn = sqlite3.connect("openexcavator.db")
    query = "INSERT INTO config(key, value) VALUES(?, ?)"
    data = [
        ("wifi_ssid", ""),
        ("wifi_psk", ""),
        ("gps_host", "127.0.0.1"),
        ("gps_port", "9000"),
        ("gps_type", "UBX"),
        ("ntrip_host", ""),
        ("ntrip_port", ""),
        ("ntrip_mountpoint", ""),
        ("ntrip_user", ""),
        ("ntrip_password", ""),
        ("imu_host", "127.0.0.1"),
        ("imu_port", "7000"),
        ("imu_type", "FXOS8700+FXAS21001"),
        ("start_altitude", "700"),
        ("stop_altitude", "800"),
        ("antenna_height", "10"),
        ("safety_depth", "690"),
        ("safety_height", "810"),
        ("output_port", "3000"),
        ("path", """{"type":"FeatureCollection","crs":{"type":"name","properties":{"name":"urn:ogc:def:crs:OGC:1.3:CRS84"}},"features":[{"type":"Feature","properties":{"name":"start","solution status":1},"geometry":{"type":"Point","coordinates":[5.415527224859864,51.6995130221744,0.2053654933964033]}},{"type":"Feature","properties":{"name":"stop","solution status":1},"geometry":{"type":"Point","coordinates":[5.415535259001904,51.69950088928952,1.4064961066623827]}}]}""")
    ]
    cursor = conn.cursor()
    for item in data:
        try:
            cursor.execute(query, item)
            conn.commit()
        except sqlite3.IntegrityError as exc:
            print("cannot insert items %s: %s" % (item[0], exc))
    conn.close()


if __name__ == "__main__":
    create_structure()
    populate_config()
