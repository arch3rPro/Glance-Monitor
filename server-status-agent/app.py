import os
import platform
import socket
import time
from datetime import datetime
from typing import List

import psutil
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

def get_real_hostname():
    # 优先读取宿主机 /etc/hostname
    try:
        with open("/host/etc/hostname") as f:
            return f.read().strip()
    except Exception:
        return socket.gethostname()

def get_boot_time():
    return int(psutil.boot_time())

def mb_to_gb(mb):
    return round(mb / 1024, 1)

def bytes_to_gb(b):
    return round(b / 1024 / 1024 / 1024, 1)

def get_cpu_info():
    load1, load5, load15 = psutil.getloadavg()
    cpu_count = psutil.cpu_count(logical=True)
    # 百分比 = 负载/核心数*100
    load1_percent = round(load1 / cpu_count * 100, 1)
    load15_percent = round(load15 / cpu_count * 100, 1)
    # 温度（部分平台支持）
    temp_c = None
    try:
        temps = psutil.sensors_temperatures()
        if temps:
            for name, entries in temps.items():
                for entry in entries:
                    if entry.current:
                        temp_c = entry.current
                        break
                if temp_c:
                    break
    except Exception:
        pass
    return {
        "Load1Percent": load1_percent,
        "Load15Percent": load15_percent,
        "TemperatureC": temp_c,
        "LoadIsAvailable": True,
        "TemperatureIsAvailable": temp_c is not None,
    }

def get_memory_info():
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()
    return {
        "IsAvailable": True,
        "UsedPercent": round(mem.percent, 1),
        "UsedGB": bytes_to_gb(mem.used),
        "TotalGB": bytes_to_gb(mem.total),
        "SwapIsAvailable": swap.total > 0,
        "SwapUsedGB": bytes_to_gb(swap.used),
        "SwapTotalGB": bytes_to_gb(swap.total),
        "SwapUsedPercent": round(swap.percent, 1) if swap.total > 0 else 0,
    }

def get_mountpoints():
    partitions = psutil.disk_partitions()
    result = []
    for p in partitions:
        try:
            usage = psutil.disk_usage(p.mountpoint)
            result.append({
                "Name": p.device,
                "Path": p.mountpoint,
                "UsedGB": bytes_to_gb(usage.used),
                "TotalGB": bytes_to_gb(usage.total),
                "UsedPercent": round(usage.percent, 1),
            })
        except Exception:
            continue
    return result

@app.get("/api/sysinfo/all")
def sysinfo():
    info = {
        "Hostname": get_real_hostname(),
        "Platform": platform.platform(),
        "BootTime": get_boot_time(),
        "HostInfoIsAvailable": True,
        "CPU": get_cpu_info(),
        "Memory": get_memory_info(),
        "Mountpoints": get_mountpoints(),
    }
    return JSONResponse(content=info) 