#!/usr/bin/env python3
"""Fetch Open-Meteo Best Match hourly forecast and atomically write forecast.json."""
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
import json
import os
import tempfile
import urllib.parse
import urllib.request

LAT = 34.98563589168014
LON = 138.07341779436342
TIMEZONE = "Asia/Tokyo"
PRESSURE_LEVELS = [1000, 975, 950, 925, 900, 850, 800, 750, 700]
OUTFILE = Path(__file__).resolve().parent / "forecast.json"


def main():
    hourly = ["temperature_2m", "relative_humidity_2m", "surface_pressure"]
    for p in PRESSURE_LEVELS:
        hourly.extend([f"temperature_{p}hPa", f"dew_point_{p}hPa", f"geopotential_height_{p}hPa"])
    params = {
        "latitude": LAT,
        "longitude": LON,
        "hourly": ",".join(hourly),
        "forecast_days": 3,
        "timezone": TIMEZONE,
        "temperature_unit": "celsius",
    }
    url = "https://api.open-meteo.com/v1/forecast?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "emagram-forecast-updater/1.0"})
    with urllib.request.urlopen(req, timeout=30) as response:
        if response.status != 200:
            raise RuntimeError(f"Open-Meteo returned HTTP {response.status}")
        api = json.loads(response.read().decode("utf-8"))

    if not isinstance(api.get("hourly", {}).get("time"), list) or not api["hourly"]["time"]:
        raise RuntimeError("Open-Meteo response has no hourly.time data")

    now = datetime.now(ZoneInfo(TIMEZONE))
    today = now.date()
    result = {
        "fetchedAt": now.strftime("%Y-%m-%d %H:%M:%S"),
        "timezone": TIMEZONE,
        "latitude": LAT,
        "longitude": LON,
        "elevation": api.get("elevation"),
        "forecastDays": [today.isoformat(), (today + timedelta(days=1)).isoformat()],
        "hourly": api["hourly"],
        "pressureLevels": PRESSURE_LEVELS,
    }
    # Write to a temporary file first; replace forecast.json only after a successful fetch/validation.
    fd, temp_name = tempfile.mkstemp(prefix="forecast-", suffix=".json", dir=str(OUTFILE.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, separators=(",", ":"))
            f.write("\n")
        os.replace(temp_name, OUTFILE)
    except Exception:
        try:
            os.unlink(temp_name)
        except OSError:
            pass
        raise
    print(f"Updated {OUTFILE.name}: fetchedAt={result['fetchedAt']}, hours={len(result['hourly']['time'])}")


if __name__ == "__main__":
    main()
