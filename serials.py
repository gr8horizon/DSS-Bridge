import subprocess
import plistlib

def get_arduino_nano_every():
    # 1. Run the system report for USB devices in XML format
    # SPUSBDataType is the standard, though some newer macOS versions 
    # may use SPUSBHostDataType internally.
    cmd = ["system_profiler", "SPUSBDataType", "-xml"]
    
    try:
        result = subprocess.run(cmd, capture_output=True, check=True)
        # 2. Parse the XML output into a Python list/dictionary
        data = plistlib.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error running system_profiler: {e}")
        return []

    devices = []
    target_pid = "0x0058"

    def find_devices(items):
        """Recursively search the USB tree for the specific Product ID."""
        for item in items:
            # Check if this item is the device we're looking for
            if item.get("product_id", "").strip() == target_pid:
                devices.append({
                    "name": item.get("_name"),
                    "serial_number": item.get("serial_num", "N/A"),
                    "location_id": item.get("location_id", "N/A"),
                    "vendor_id": item.get("vendor_id", "N/A")
                })
            
            # USB devices are often nested (e.g., behind hubs), so we recurse
            if "_items" in item:
                find_devices(item["_items"])

    # The top level is a list of data types; we iterate through them
    for top_level in data:
        if "_items" in top_level:
            find_devices(top_level["_items"])

    return devices

# --- Execution ---
if __name__ == "__main__":
    arduino_list = get_arduino_nano_every()
    
    if arduino_list:
        print(f"Found {len(arduino_list)} Arduino Nano Every device(s):")
        for dev in arduino_list:
            print(f"\nDevice: {dev['name']}")
            print(f"  Serial Number: {dev['serial_number']}")
            print(f"  Location ID:   {dev['location_id']}")
    else:
        print("No Arduino Nano Every (0x0058) found.")


        



# import os, sys, subprocess, json

# a = json.loads(subprocess.check_output('system_profiler -json SPUSBDataType', shell=True))
# # print(json.dumps(a, indent=2))

# def item_generator(json_input, lookup_key):
#     if isinstance(json_input, dict):
#         for k, v in json_input.items():
#             if k == lookup_key:
#                 yield v
#             else:
#                 yield from item_generator(v, lookup_key)
#     elif isinstance(json_input, list):
#         for item in json_input:
#             yield from item_generator(item, lookup_key)

# for _ in item_generator(a, 'manufacturer'):
# 	print(_)
