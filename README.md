# openexcavator

## About
The application is intended to be used with a high precision GPS receiver for assisting excavation operations (assist with bucket positioning for land leveling, trenching).  
When IMU data (roll, pitch, yaw) is available it will be used together with antenna height to determine the bucket position more precisely.  
It uses a thread for reading GPS data and a thread for reading IMU data; on the web part it's using the Tornado web framework and Bootstrap 4 and Leaflet libraries.  
It is designed to run on a Raspberry Pi (but can run on other devices as well) and present a web interface used by the operator on a smartphone / tablet / notebook PC.

---
## Installation
Install dependencies:
```
sudo apt-get install -y python3-pip python3-dev
sudo apt-get install -y dnsmasq hostapd #for Wi-Fi management if desired
sudo pip3 install tornado utm
```
Since the application has a restart function it needs to run unde the Pi user:
```
sudo mkdir /var/www
sudo chown -R pi:pi /var/www
cd /var/www
git clone https://github.com/GwnDaan/openexcavator .
python3 openexcavator/database.py #initialize database entries
```
To enable the application to start at boot copy the `openexcavator.service` systemd file from the `scripts` folder to `/etc/systemd/system` and enable it using:
```
sudo cp /var/www/openexcavator/scripts/openexcavator.service /etc/systemd/system/
sudo systemctl daemon-reload  
sudo systemctl enable openexcavator && sudo systemctl start openexcavator
```
Check the logs to be sure the application is working as expected:
```
journalctl -f -u openexcavator
``` 
You should now be able to access the web interface on: https://ip-of-raspberry:8000/

---
## Wi-Fi
The application can manage Wi-Fi connectivity so it can work with an existing network or standalone (in hotspot mode).  
In order to manage the connectivity it needs an SSID and password defined (see Settings -> `Wi-Fi SSID` and `PWD`).  
`openexcavator` handles writing the `wpa_supplicant` file (needed to connect to existing networks) at runtime with the network defined in the _Settings_ page but the user must manually create the following files upon installation (only needed once):    
```
sudo cp /var/www/openexcavator/scripts/dnsmasq.conf /etc/dnsmasq.conf
sudo cp /var/www/openexcavator/scripts/hostapd.conf /etc/hostapd/hostapd.conf
```
Afterwards edit `/etc/dhcpcd.conf` and add the following lines:
```
#openexcavator config
ssid openexcavator
static ip_address=192.168.173.1/24
static routers=192.168.173.1
static domain_name_servers=192.168.173.1
```
Default hotspot SSID is `openexcavator` while the password is `somepass`; default IP address for the Pi is `192.168.173.1`.  
Of course you can change the hotspot SSID and password if you need to; IP addresses can also be changed but make sure you edit both `dnsmasq` and `dhcpcd` files.   
Reboot the Pi after installation and upon restart it should start managing Wi-Fi connectivity.

---
## GPS Receiver
TODO: add reach gps receiver setup.  
Afterwards just make sure *GPS Host* and *Port* settings are correct and you should see GPS data (*longitude*, *latitude* and *altitude*) in the web application.

### UBX Receiver
The following libraries are required to use this GPS receiver.
```
sudo pip3 install --upgrade pyubx2
```
**Note:** there are still some undocumented steps required to use this receiver.

---
## IMU
TODO: add imu setup of Reach.  
Afterwards just make sure *IMU Host* and *Port* settings are correct and you should see IMU data (*roll*, *pitch* and *yaw*) in the web application.
### Ardafruit FXOS8700+FXAS21001 
The following libraries are required to use this IMU.
```
sudo pip3 install --upgrade adafruit-python-shell
sudo pip3 install adafruit-circuitpython-fxos8700 adafruit-circuitpython-fxas21002c
sudo apt-get install -y libatlas-base-dev git
sudo pip3 install git+https://github.com/Mayitzin/ahrs
```
Next we need to enable the I2C port on the Raspberry PI.
```
sudo nano /boot/config.txt
```
Then uncomment/add the following line:
```
dtparam=i2c_arm=on
```
**Note:** there are still some undocumented steps required to use this IMU.

## Multi IMU
Multiple IMU's can be used in combination with the TCA9548 I2C multiplexer.

The following libraries need to be installed to use the multiplexer:
```
sudo pip3 install adafruit-circuitpython-tca9548a
```
TODO: add configuration steps
---
## nginx
While not strictly necessary it's a good idea to put `nginx` in front of the web application.  
To be able to serve **cached tiles** for the map, installing nginx is mandatory. By default it caches up to 2 GB of tiles for one year so loading the map once before going into hotspot mode should make the tiles available later on.
```
sudo cp /var/www/openexcavator/scripts/nginx.conf /etc/nginx/sites-available/openexcavator
sudo ln -s /etc/nginx/sites-available/openexcavator /etc/nginx/sites-enabled/
sudo cp /var/www/openexcavator/scripts/tile_cache.conf /etc/nginx/conf.d/
```
estart nginx using: `sudo systemctl restart nginx` and access the web application at `http://openexcavator/` 

---
## Code
 - the main module is `openexcavator.py` which starts the GPS and IMU threads and initializes the web application  
 - `settings.py` contains the Tornado-specific values (host, port to listen on, template and static paths)  
 - `database.py` holds database functions used to retrieve and update the configuration values (such as GPS host and port, IMU host and port, designated path, antenna height, safety height and start/stop altitude values); these values are stored in a SQLite3 database (`openexcavator.db`)  
 - `handlers.py` contains the implementation for the web application requests (render `home.html` and `tools.html`, return new position & IMU data from the threads, update configuration and restart application)  
 - `wifimanager.py` starts a thread to control Wi-Fi connectivity (enables hotspot when preferred network is not available)  
 -  the application uses Javascript for map rendering and data calculations (relevant files in the `static` folder are `common.js`, `home.js`, `tools.js`)  
 -  the `scripts` folder contains the `systemd` service definition for openexcavator  
 - TODO: add imu/gps code files
