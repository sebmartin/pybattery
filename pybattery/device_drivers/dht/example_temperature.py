import time
import glob
import pigpio
import dht11

# ----------------------------
# DHT11 (GPIO 4)
# ----------------------------

def read_dht11(gpio=4):
    """
    Returns (temperature_c, humidity) or (None, None) on failure
    """
    pi = pigpio.pi()
    if not pi.connected:
        raise RuntimeError("pigpio daemon not running")

    sensor = dht11.DHT11(pin=gpio, pi=pi)
    result = sensor.read()

    pi.stop()

    if result.is_valid():
        return result.temperature, result.humidity
    else:
        return None, None


# ----------------------------
# DS18B20 (1-Wire, all sensors)
# ----------------------------

def read_ds18b20_all():
    """
    Returns dict: { sensor_id: temperature_c }
    """
    base_path = "/sys/bus/w1/devices/"
    sensors = glob.glob(base_path + "28-*")

    readings = {}

    for sensor in sensors:
        try:
            with open(sensor + "/temperature", "r") as f:
                temp_milli_c = int(f.read().strip())
                readings[sensor.split("/")[-1]] = temp_milli_c / 1000.0
        except (OSError, ValueError):
            readings[sensor.split("/")[-1]] = None

    return readings


# ----------------------------
# Example usage
# ----------------------------

if __name__ == "__main__":
    # DHT11
    # temp, humidity = read_dht11()
    # if temp is not None:
    #     print(f"DHT11 → {temp} °C, {humidity} %")
    # else:
    #     print("DHT11 → read failed")

    # DS18B20
    ds_readings = read_ds18b20_all()
    print(ds_readings)
    for sensor_id, temp in ds_readings.items():
        print(f"DS18B20 {sensor_id} → {temp} °C")

    time.sleep(2)
