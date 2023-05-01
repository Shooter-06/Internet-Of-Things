import bluetooth

# Search for nearby Bluetooth devices for 15 seconds
nearby_devices = bluetooth.discover_devices(duration=15)

# Print the list of nearby devices
for device in nearby_devices:
    print("Device name:", bluetooth.lookup_name(device))
    print("Device address:", device)