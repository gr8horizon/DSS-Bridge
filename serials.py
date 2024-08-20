import os, sys, subprocess, json

a = json.loads(subprocess.check_output('system_profiler -json SPUSBDataType', shell=True))
# print(json.dumps(a, indent=2))

def item_generator(json_input, lookup_key):
    if isinstance(json_input, dict):
        for k, v in json_input.items():
            if k == lookup_key:
                yield v
            else:
                yield from item_generator(v, lookup_key)
    elif isinstance(json_input, list):
        for item in json_input:
            yield from item_generator(item, lookup_key)

for _ in item_generator(a, 'manufacturer'):
	print(_)
