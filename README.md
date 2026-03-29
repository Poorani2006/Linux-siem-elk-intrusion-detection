# Linux SIEM with ELK Stack

Linux-based SIEM system using ELK Stack for log analysis, SSH brute-force detection, and real-time security monitoring.

---

## Project Structure
scripts/
├── auth_log_analyzer.py
├── syslog_analyzer.py
├── kernel_log_analyzer.py
screenshots/
├── Authentication Log Image
├── kernel log image
├── kibana index management
├── service log image


---

## Screenshots

### Authentication Logs
![Authentication Log](screenshots/Authentication Log Image)

### System Logs
![Syslog](screenshots/service log image)

### Kernel Logs
![Kernel Logs](screenshots/kernel log image)

### Kibana Index Management
![Kibana](screenshots/kibana index management)

---

## How to Run

```bash
cd scripts
python3 auth_log_analyzer.py
python3 syslog_analyzer.py
python3 kernel_log_analyzer.py


Requirements
Linux OS (Debian/Ubuntu/Kali recommended)
Python 3
ELK Stack: Elasticsearch, Logstash, Kibana
Filebeat
Highlights
SSH brute-force detection using auth logs
System activity monitoring via syslog
Kernel-level event monitoring
Real-time dashboards in Kibana
Alerts for suspicious activity



