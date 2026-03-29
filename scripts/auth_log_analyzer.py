import time
from datetime import datetime
import subprocess
import json
import os
import re
from ipaddress import ip_address, IPv4Address, IPv6Address
from collections import defaultdict

failed = 0
count = defaultdict(int)  # Track attempts per IP
block = {}
block_timing = 180  # 3 minutes block timing
today = datetime.now().strftime("%d-%m-%y")
log_file = "/home/kali/Project/ssh_logs.json"

def normalize_ip(ip_str):
    """Normalize IPv4 and IPv6 addresses to consistent format"""
    if not ip_str:
        return None
    
    # Remove trailing punctuation
    ip_str = ip_str.rstrip(',:;')
    
    try:
        # Try to parse as IP address
        ip = ip_address(ip_str)
        
        # Handle IPv4
        if isinstance(ip, IPv4Address):
            return str(ip)
        
        # Handle IPv6 - normalize to compressed format
        elif isinstance(ip, IPv6Address):
            # Convert to lowercase and compress
            normalized = ip.compressed.lower()
            # Handle ::1 specifically
            if normalized == '::1':
                return '::1'
            return normalized
            
    except ValueError:
        # Not a valid IP address
        return None

def is_valid_ip(ip_str):
    """Check if string is valid IP address"""
    if not ip_str:
        return False
    try:
        ip_address(ip_str.rstrip(',:;'))
        return True
    except ValueError:
        return False

def parse_log_timestamp(log_line, calculate):
    """Parse the actual timestamp from the log line"""
    try:
        # Try to get timestamp from first 3 fields (e.g., "Mar 25 09:14:50")
        if len(calculate) >= 3:
            # Get the date components
            month = calculate[0]
            day = calculate[1]
            time_str = calculate[2]
            
            # Create timestamp string
            current_year = datetime.now().year
            timestamp_str = f"{current_year} {month} {day} {time_str}"
            
            # Parse to datetime
            dt = datetime.strptime(timestamp_str, "%Y %b %d %H:%M:%S")
            
            return dt.isoformat(), f"{month} {day} {time_str}"
    except Exception as e:
        print(f"[DEBUG] Timestamp parse error: {e}")
    
    # Fallback to current time
    return datetime.now().isoformat(), "Unknown time"

def extract_ip_from_line(line, calculate):
    """Extract IP address from log line using multiple methods"""
    ip = None
    
    # Method 1: Look for 'from' keyword
    if "from" in calculate:
        try:
            ip_idx = calculate.index("from") + 1
            if ip_idx < len(calculate):
                potential_ip = calculate[ip_idx].rstrip(',:;')
                if is_valid_ip(potential_ip):
                    ip = potential_ip
                    print(f"[DEBUG] Found IP after 'from': {ip}")
        except (ValueError, IndexError):
            pass
    
    # Method 2: Look for IP pattern (both IPv4 and IPv6)
    if not ip:
        # IPv4 pattern
        ipv4_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
        ipv4_matches = re.findall(ipv4_pattern, line)
        for match in ipv4_matches:
            if is_valid_ip(match):
                ip = match
                print(f"[DEBUG] Found IPv4 via regex: {ip}")
                break
    
    if not ip:
        # IPv6 pattern
        ipv6_pattern = r'\b(?:[0-9a-fA-F]{1,4}:){1,7}[0-9a-fA-F]{1,4}\b'
        ipv6_matches = re.findall(ipv6_pattern, line)
        for match in ipv6_matches:
            if is_valid_ip(match):
                ip = match
                print(f"[DEBUG] Found IPv6 via regex: {ip}")
                break
    
    # Normalize if found
    if ip:
        ip = normalize_ip(ip)
    
    return ip

def extract_port(calculate):
    """Extract port number from log line"""
    if "port" in calculate:
        try:
            port_idx = calculate.index("port") + 1
            if port_idx < len(calculate):
                port_str = calculate[port_idx].rstrip(',:;')
                if port_str.isdigit():
                    return int(port_str)  # Return as integer
        except (ValueError, IndexError):
            pass
    return None  # Return None instead of "Unknown" for better JSON typing

def extract_user(calculate):
    """Extract username from failed login attempt"""
    try:
        # Pattern: "Failed password for USER from IP"
        if "for" in calculate:
            for_idx = calculate.index("for") + 1
            if for_idx < len(calculate) and calculate[for_idx] != "invalid":
                return calculate[for_idx]
    except ValueError:
        pass
    return "unknown"

def read_existing_ips():
    """Read existing IPs from JSON file to avoid duplicates in current run"""
    existing_ips = set()
    if os.path.exists(log_file):
        try:
            with open(log_file, 'r') as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        if 'ip' in data:
                            existing_ips.add(data['ip'])
        except (json.JSONDecodeError, FileNotFoundError):
            pass
    return existing_ips

try:
    # Try different service names
    service_name = "ssh"
    result = subprocess.run(
        ["journalctl", "-u", service_name, "--since", "5 minutes ago", "--no-pager"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # If ssh service doesn't have logs, try sshd
    if result.returncode != 0 or not result.stdout.strip():
        result = subprocess.run(
            ["journalctl", "-u", "sshd", "--since", "5 minutes ago", "--no-pager"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if result.stdout.strip():
            print("Using sshd service logs\n")

    lines = result.stdout.split("\n")
    print(f"Processing {len(lines)} log lines...\n")
    
    # Track processed entries to avoid duplicates in same run
    processed_entries = set()
    
    # Read existing IPs to avoid counting them again
    existing_ips = read_existing_ips()
    
    for line in lines:
        if "Failed password" in line:
            calculate = line.split()
            current_time = time.time()
            
            # Parse actual timestamp from log
            iso_timestamp, log_time = parse_log_timestamp(line, calculate)
            
            # Extract IP
            ip = extract_ip_from_line(line, calculate)
            
            # Extract port
            port = extract_port(calculate)
            
            # Extract username
            username = extract_user(calculate)
            
            # Create unique key to avoid processing same entry multiple times
            entry_key = f"{line[:100]}"  # Use first 100 chars as unique identifier
            if entry_key in processed_entries:
                continue
            processed_entries.add(entry_key)
            
            if ip:
                # Increment count only if this IP is new in this run
                # For accurate counting, we should use a time window approach
                count[ip] += 1
                
                print(f"[DEBUG] IP {ip} now has {count[ip]} attempts (from this run)")
                
                # BRUTE FORCE DETECTION (based on current run)
                if count[ip] == 5:
                    block[ip] = current_time
                    print(f"\n[ALERT ] {log_time} → IP {ip} has {count[ip]} failed attempts")
                    print(f"[ALERT] Suspicious activity detected from {ip}\n")
                    
                    # Write to alert log
                    with open("alert_ip_" + today + ".log", "a") as f:
                        f.write(f"{log_time} {ip} {count[ip]} Attempts for login\n")
                
                # JSON OUTPUT - Clean structure for ELK
                log_data = {
                    "@timestamp": iso_timestamp,  # Use actual log timestamp, not current time
                    "log_time": log_time,
                    "event": "failed_login",
                    "ip": ip,
                    "user": username,
                    "port": port if port is not None else 0,  # Use integer 0 for unknown
                    "status": "failed",
                    "attempt_count": count.get(ip, 0),
                    "alert": count.get(ip, 0) >= 5,
                    "host": {
                        "name": "kali"
                    },
                    "log": {
                        "file": {
                            "path": "/var/log/journal"
                        }
                    }
                }
                
                # Remove None values to keep JSON clean
                log_data = {k: v for k, v in log_data.items() if v is not None}
                
                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(log_file) if os.path.dirname(log_file) else '.', exist_ok=True)
                
                # Write to JSON file (append mode)
                with open(log_file, "a") as f:
                    f.write(json.dumps(log_data) + "\n")
                    print(f"[DEBUG] Wrote to JSON: {json.dumps(log_data, indent=2)}")
                
                # Print to console
                port_str = f"Port: {port}" if port else "Port: Unknown"
                print(f"{log_time} | IP: {ip} | {port_str} | User: {username} | Failed Login (Attempt #{count[ip]})")
            else:
                print(f"{log_time} | IP: NOT_FOUND | Failed Login")
                failed += 1  # Count failed logins without IP as well
        
        # UNBLOCK LOGIC
        if 'current_time' in locals():
            for blocked_ip in list(block.keys()):
                if current_time - block[blocked_ip] > block_timing:
                    print(f"[INFO] {blocked_ip} unblocked after {block_timing} seconds")
                    del block[blocked_ip]
    
    # Summary
    print("\n" + "="*50)
    print(f"Total Failed Attempts in this run: {failed}")
    print(f"Total Unique IPs with failures: {len(count)}")
    
    if count:
        print("\nAttempts per IP (this run):")
        for ip, attempts in sorted(count.items(), key=lambda x: x[1], reverse=True):
            print(f"  {ip}: {attempts} attempts")
            
            # Additional alert for high number of attempts
            if attempts >= 10:
                print(f"      HIGH RISK: {ip} has {attempts} failed attempts!")
    
    # Show blocked IPs if any
    if block:
        print(f"\nCurrently blocked IPs:")
        for blocked_ip in block.keys():
            time_remaining = block_timing - (current_time - block[blocked_ip])
            print(f"  {blocked_ip}: {int(time_remaining)} seconds remaining")
    
    # Show JSON file location
    if os.path.exists(log_file):
        file_size = os.path.getsize(log_file)
        print(f"\n JSON log file: {log_file}")
        print(f"   Size: {file_size} bytes")
        
        # Count total entries
        with open(log_file, 'r') as f:
            total_entries = sum(1 for line in f if line.strip())
        print(f"   Total entries: {total_entries}")

except Exception as e:
    print("Error:", e)
    import traceback
    traceback.print_exc()
