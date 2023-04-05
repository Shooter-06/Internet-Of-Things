# PyBluez example: device_inquiry.py
# Performs a device inquiry followed by a remote name request of each discovered device
# Author: fr
# Date: 2023-03-31

import bluetooth

print("Performing device inquiry...")

# Discover Bluetooth devices for 10 seconds, look up their names, and flush the cache.
nearby_devices = bluetooth.discover_devices(duration=10, lookup_names=True, flush_cache=True, lookup_class=False)

# Print the number of discovered devices
print("Found {} devices".format(len(nearby_devices)))

# For each discovered device, print its Bluetooth address and name (if available).
for addr, name in nearby_devices:
    print("Device name: {} - address: {}".format(name, addr))
