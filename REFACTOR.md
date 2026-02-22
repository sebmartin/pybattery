# Refactor: `device_types` → `device_drivers`

Refactor the `pybattery` codebase to rename and restructure the device abstraction layer. The goal is to make the naming more precise (devices have *drivers*, not *types*) and to give each driver its own package directory so related files can be co-located.

---

## Requirements

### 1. Rename the concept throughout the codebase

Every reference to "device type" should become "device driver". This includes:

- Directory names
- Module names
- Class names
- Variable and property names
- Config file field names (`type:` → `driver:`)
- CLI subcommand names
- Any user-facing output strings (e.g. YAML keys in command output)

### 2. Restructure each driver as a package

Currently each device is a single flat `.py` file inside `device_types/`. After the refactor, each device should be a subdirectory package inside `device_drivers/`. This allows related files (models, hardware abstractions, tests, etc.) to live together.

The package discovery mechanism should still work automatically — adding a new driver directory should make it available without any changes to core code.

### 3. DHT11 driver: replace `Adafruit_DHT` with `pigpio`

The current `dht11.py` uses the `Adafruit_DHT` library which is no longer maintained and does not install cleanly on Python 3.12. Replace it with a `pigpio`-based implementation that:

- Reads DHT sensor data by listening to GPIO rising edges
- Supports DHT11 and generic DHTXX models
- Uses pydantic to validate driver configuration
- Returns structured data (timestamp, status, temperature, humidity)
- Returns a safe error result (rather than crashing) if the sensor read fails

### 4. DS18B20 driver: replace stub with real implementation

The current `ds12b20.py` (note: this name has a typo) is a stub that returns `{}`. Replace it with a real implementation that:

- Fixes the typo in the driver name (`ds18b20`)
- Reads temperature from the Linux one-wire interface at `/sys/bus/w1/devices`
- Validates that the configured sensor ID actually exists on the system at startup, raising a descriptive error if not
- Uses pydantic to validate driver configuration

### 5. LCD driver: decouple from RPi-specific hardware imports

The current `lcd.py` imports `RPLCD` and `RPi.GPIO` at module level, which causes `ImportError` on non-Raspberry Pi systems. Refactor it so that:

- The hardware import is deferred and wrapped in a try/except
- A fake/stub LCD implementation is used as a fallback when the real library is unavailable
- The driver can be imported and tested on any machine

### 6. Add a utility for Raspberry Pi detection

Add a module that provides helper functions to:

- Detect whether the code is running on a Raspberry Pi
- Determine whether fake/stub hardware is allowed (either because we're on an RPi, or an environment variable opt-in is set)
- Raise an appropriate error when real hardware is required but unavailable

This should be used by the LCD and any other drivers that need platform-conditional behavior.

### 7. Improve CLI and API

- Remove the `list-gpio` subcommand (it was broken and unused)
- The `write` command should be fully implemented end-to-end (currently it only prints a message)
- Configuration loading errors should be caught and displayed cleanly, not as unhandled exceptions

### 8. Python version and tooling

- Upgrade from Python 3.8 to Python 3.12
- Migrate from `setup.py`-only to `pyproject.toml` using `uv`
- Add separate dependency groups for dev and RPi-specific dependencies (the RPi packages should not be required on non-Pi systems)

### 9. Write tests for each driver

Each driver should have tests that run on macOS without real hardware and achieve maximum code coverage of the driver logic. The LCD driver is excluded from this requirement for now.

Use types throughout — typed config models, typed Protocols for hardware abstractions, and type hints on all functions. Hardware dependencies should be abstracted so the real driver logic can be exercised in tests without any physical device.

---

## Desired Outcomes

- `pybattery devices` lists all configured devices
- `pybattery drivers` lists all available device drivers
- All code (including driver modules) can be imported and tested on macOS/Linux without a Raspberry Pi, as long as the `ALLOW_FAKE_DEVICES` env var is set
- Tests pass on non-RPi systems
- Adding a new driver only requires creating a new subdirectory under `device_drivers/` — no changes to core discovery or CLI code
