import asyncio
import time
from datetime import datetime
from bleak import discover
import yaml
import pprint
import os

# Configurations
config = yaml.safe_load(open(os.path.join(os.path.dirname(__file__), 'config.yml')))
try:
    secrets = yaml.safe_load(open(os.path.join(os.path.dirname(__file__), 'secrets.yml')))
except:
    secrets = None

# Function to discover our devices
async def discover_device():
    all_devices = await discover(timeout=config['timeout'])
    devices = []
    for d in all_devices:
        if 'manufacturer_data' in d.metadata.keys() and 65535 in d.metadata['manufacturer_data'].keys():
            # Specific device with CO2 sensor
            if d.metadata['manufacturer_data'][65535][0] == 2 and d.metadata['manufacturer_data'][65535][1] == 236:
                devices.append(d)
    return devices

# Function to parse sensor data from devices
def parse_sensor_data(devices):
    readings = []
    for d in devices:
        data = d.metadata['manufacturer_data'][65535]
        readings.append(
            dict(
                timestamp=datetime.now(),
                mac=d.address,
                stat = data[2], # stat
                co2 = data[4]*256 + data[3], # co2 ppm
                temp = (data[6]*256 + data[5])/100, # temperature in deg C
                humi = (data[8]*256 + data[7])/100, # humidity % RH
                press = (data[11]*256*256 + data[10]*256 + data[9])/100, # pressure in Pa
                photo = (data[13]*256 + data[12]), # radiation ADC
                batt = (data[15]*256 + data[14]), # battery, mV
                swVers = data[16] & 7,
                hwVers = data[16] >> 4,
            )
        )
    return readings
  
# Function to print sensor readings
def print_sensor_reading(readings):
    for r in readings:
        current_time = datetime.strftime(r['timestamp'], '%Y-%m-%d %H:%M:%S')
        print(f"{current_time}:  Device: {r['mac']}, CO2: {r['co2']} ppm, " +
              f"T: {r['temp']:.2f} deg, RH: {r['humi']:.2f}%, " +
              f"P: {r['press']:.2f} Pa, Rad: {r['photo']}, " +
              f"Battery: {r['batt']} mV."
              )

# Function to write to csv file
def write_to_csv(readings):
    for r in readings:
        filename = os.path.join(os.path.dirname(__file__), config['path'], f"data_{r['mac'].replace(':','_')}.csv")
        # Check if file exists
        if not os.path.isfile(filename):
            with open(filename, 'a') as f:
                f.write(f"Datetime,CO2 (ppm),T (°C),RH (%),P (Pa),Ambient Light (ADC),Battery (mV)\n")
        with open(filename, 'a') as f:
            f.write(f"{r['timestamp']},{r['co2']},{r['temp']},{r['humi']},{r['press']},{r['photo']},{r['batt']}\n")
        
# Function to send alert to mattermost
def send_alert(readings):
    for r in readings:
        if 'E7' in r['mac'] and r['co2'] > config['alert_co2']:
            payload = '{\"text\": \"**High CO2 alert!** :skull:\n' + '\tCO2 = ' + str(r['co2']) + ' ppm\"}'
            if secrets:
                os.popen(f"curl -X POST --data-urlencode 'payload={payload}' {secrets['mattermost_url']}")
            else:
                print(payload)
        
# Function to run all functions        
async def run():
    print('EmpAIR: Multi-sensor bluetooth device.')
    print("Settings:")
    pprint.pprint(config)
    
    print("Starting sensor analysis...")
    while True:
        start_time = time.time()    
        # Discover devices
        devices = await discover_device()
        
        if len(devices) > 0:
            # Read sensor data
            readings = parse_sensor_data(devices)
            # Print readings
            if config['console']:
                print_sensor_reading(readings)
            # Write to csv file
            if config['store']:
                write_to_csv(readings)
            # rsync to remote server
            if config['sync']:
                os.popen(f"rsync -avhu {os.path.join(os.path.dirname(__file__), config['path'])} {config['sync_path']}")
            # Alert to mattermost
            if config['alert']:
                send_alert(readings)
                
            # Sleep for a while
            remaining_time = config['log_interval'] - (time.time() - start_time)
            if remaining_time > 0:
                await asyncio.sleep(remaining_time)
        else:
            print("No devices found.")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
