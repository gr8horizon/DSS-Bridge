import json, subprocess

p = json.loads(subprocess.check_output('system_profiler -json SPUSBDataType', shell=True))
print(p)
