import json
import subprocess
from datetime import datetime

# File to store JSON logs automatically
output_file = "/home/kali/Project/kernel_logs.json"

# Counters
error=0
fail=0
IO_error=0
EXT4_fs=0
buffer_IO=0
Kernel_panic=0
not_syncing=0
out_of_memory=0
killed_process=0
segfault=0
CPU_error=0
disk_failure=0
driver=0
counter=0

def process_line(line):
    global error, fail, IO_error, EXT4_fs, buffer_IO, Kernel_panic
    global not_syncing, out_of_memory, killed_process, segfault
    global CPU_error, disk_failure, driver, counter

    line_lower = line.lower()
    timestamp = datetime.now().isoformat()
    record = None

    if "error" in line_lower:
        error += 1
        counter += 1
        record = {"time": timestamp, "type": "Kernel Errors Detected", "count": error}

    if "fail" in line_lower:
        fail += 1
        counter += 1
        record = {"time": timestamp, "type": "Kernel Fail Detected", "count": fail}

    if "i/o error" in line_lower:
        IO_error += 1
        counter += 1
        record = {"time": timestamp, "type": "Kernel I/O Error Detected", "count": IO_error}

    if "ext4-fs" in line_lower:
        EXT4_fs += 1
        counter += 1
        record = {"time": timestamp, "type": "Kernel EXT4-fs Detected", "count": EXT4_fs}

    if "buffer i/o" in line_lower:
        buffer_IO += 1
        counter += 1
        record = {"time": timestamp, "type": "Kernel Buffer I/O Detected", "count": buffer_IO}

    if "kernel panic" in line_lower:
        Kernel_panic += 1
        counter += 1
        record = {"time": timestamp, "type": "Kernel panic Detected", "count": Kernel_panic}

    if "not syncing" in line_lower:
        not_syncing += 1
        counter += 1
        record = {"time": timestamp, "type": "Kernel Not syncing Detected", "count": not_syncing}

    if "out of memory" in line_lower:
        out_of_memory += 1
        counter += 1
        record = {"time": timestamp, "type": "Kernel Out of memory Detected", "count": out_of_memory}

    if "killed process" in line_lower:
        killed_process += 1
        counter += 1
        record = {"time": timestamp, "type": "Kernel Killed process Detected", "count": killed_process}

    if "segfault" in line_lower:
        segfault += 1
        counter += 1
        record = {"time": timestamp, "type": "Kernel Segfault Detected", "count": segfault}

    if "cpu error" in line_lower:
        CPU_error += 1
        counter += 1
        record = {"time": timestamp, "type": "Kernel CPU error Detected", "count": CPU_error}

    if "disk failure" in line_lower:
        disk_failure += 1
        counter += 1
        record = {"time": timestamp, "type": "Kernel Disk failure Detected", "count": disk_failure}

    if "driver" in line_lower:
        driver += 1
        counter += 1
        record = {"time": timestamp, "type": "Kernel Driver Detected", "count": driver}

    return record

try:
    with open(output_file, "a") as json_file:

        # Step 1: Process recent logs quickly (last 1000 lines)
        recent_logs = subprocess.run(
            ["journalctl", "-k", "-n", "1000", "-o", "short"],
            capture_output=True, text=True
        ).stdout.splitlines()

        for line in recent_logs:
            record = process_line(line)
            if record:
                json_file.write(json.dumps(record) + "\n")
                json_file.flush()

        # Step 2: Switch to real-time monitoring
        with subprocess.Popen(["journalctl", "-kf", "-o", "short"], stdout=subprocess.PIPE, text=True) as proc:
            for line in proc.stdout:
                record = process_line(line)
                if record:
                    json_file.write(json.dumps(record) + "\n")
                    json_file.flush()

except Exception as e:
    print(json.dumps({"error": str(e)}))
