import time
import json
import subprocess
from datetime import datetime

log_file="/home/kali/Project/service.log"
output_file="/home/kali/Project/service_output.json"

today=datetime.now().strftime("%d-%m-%y")

services_data={
    "sshd":{"start":0,"stop":0,"failure":0,"found":False},
    "cron":{"start":0,"stop":0,"failure":0,"found":False},
    "network":{"start":0,"stop":0,"failure":0,"found":False},
    "apache2":{"start":0,"stop":0,"failure":0,"found":False},
    "systemd":{"start":0,"stop":0,"failure":0,"found":False},
    "rsyslog":{"start":0,"stop":0,"failure":0,"found":False}
}

try:

    print(" Live Service Monitoring Started...")

    process = subprocess.Popen(
        ["journalctl","-f","-n","50"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    for line in process.stdout:

        line_lower=line.lower() or (service=="sshd" and "ssh" in line_lower)
        event_detected=False

        for service in services_data.keys():

            if service in line_lower or (service=="apache2" and "nginx" in line_lower):

                services_data[service]["found"]=True

                if "started" in line_lower:
                    services_data[service]["start"]+=1
                    event_detected=True

                if "stopped" in line_lower:
                    services_data[service]["stop"]+=1
                    event_detected=True

                if "failed" in line_lower or "failure" in line_lower:
                    services_data[service]["failure"]+=1
                    event_detected=True

                if event_detected:
                    print(f" {service} -> S:{services_data[service]['start']}  T:{services_data[service]['stop']}  F:{services_data[service]['failure']}")

        soc_output={
            "date":today,
            "timestamp":datetime.now().isoformat(),
            "service_monitoring":services_data
        }

        with open(output_file,"w") as json_file:
            json.dump(soc_output,json_file,indent=4)

except Exception as e:
    print("Error:",e)
