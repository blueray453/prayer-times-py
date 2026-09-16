.If Edit
pipx install --force --editable /media/ismail/SSDWorking/_Working/_MyProjects/prayer-times-py

pip freeze > requirements.txt

pip install -r requirements.txt

mkdir -p ~/.local/share/applications
mkdir -p ~/.local/share/icons/hicolor/256x256/apps

SRC=/media/ismail/SSDWorking/_Working/_MyProjects/prayer-times-py

cp "$SRC/prayer-times.desktop" ~/.local/share/applications/
cp "$SRC/icons/mosque.png"     ~/.local/share/icons/hicolor/256x256/apps/
cp "$SRC/icons/mosque.png"     ~/.local/share/icons/

update-desktop-database ~/.local/share/applications
gtk-update-icon-cache -f -t ~/.local/share/icons/hicolor

.Verify
ls -l ~/.local/share/applications/prayer-times.desktop
ls -l ~/.local/share/icons/mosque.png
ls -l ~/.local/share/icons/hicolor/256x256/apps/mosque.png
desktop-file-validate ~/.local/share/applications/prayer-times.desktop

python -m venv .venv
.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
python prayer-times-gui.py

pyproject.toml so that you can use `pip install .`

python prayer-times-cli.py \
  --lat 23.836468 --lon 90.3695392 --tz Asia/Dhaka --date 2026-09-16 \
  --fajr-angle 18.0 --isha-angle 17.0 --asr-ratio 1.0

python prayer-times-cli.py \
  --lat 23.836468 --lon 90.3695392 --tz Asia/Dhaka --date 2026-09-16 \
  --asr-ratio 1.0 --pcd

python prayer-times-cli.py \
  --lat 23.836468 --lon 90.3695392 --tz Asia/Dhaka --date 2026-09-16 \
  --asr-ratio 1.0 --spa

% python prayer-times-regular-cli.py \
  --lat 23.836468 --lon 90.3695392 --tz Asia/Dhaka --date 2026-09-16 \
  --fajr-angle 18.0 --isha-angle 17.0 --asr-ratio 1.0

% python prayer-times-pcd-cli.py \
  --lat 23.836468 --lon 90.3695392 --tz Asia/Dhaka --date 2026-09-16 \
  --asr-ratio 1.0

% python prayer-times-spa-cli.py \
  --lat 23.836468 --lon 90.3695392 --tz Asia/Dhaka --date 2026-09-16 \
  --asr-ratio 1.0

* Two proxies (Fajr/Isha angles) affect the five obligatory prayers.
* Five additional proxies (spear-alt, duha-alt, yellow-alt, zenith-before, zenith-after, asr-early-min) affect the voluntary-prayer windows, the best-time recommendations, and the forbidden intervals.
* Everything else — solar position, sunrise, sunset, solar noon, night fractions, Asr shadow-ratio time — is computed exactly from astronomy and hadith.

NOTE: The sun is usually white bright that you can’t look into it. when it becomes yellow, this means that it is not that bright and you can look at it.

# Short Answer: No — There Are Several Other Proxies, Not Just Two

Your statement is not quite correct. `--fajr-angle` and `--isha-angle` are not the only calibration constants. There are **five more** in your current CLI. Here is the honest breakdown by tier.

## Tier 1 — Pure Calculation (Astronomy Gives the Number)

These are derived from the sun's position and need no calibration beyond lat/lon/date:

| Value | Computed From |
| :--- | :--- |
| Solar declination | SPA / Meeus ephemeris |
| Equation of time | Same |
| Solar noon (Istiwa' / Zawal) | Longitude + EoT |
| Sunrise, sunset | Hour angle at −0.833° |
| Asr time | Hour angle at shadow ratio altitude |
| Night length | Maghrib → Fajr |
| Last third of night | ⅔ of night length |
| Midnight | ½ of night length |

These are exact to the second. No calibration.

## Tier 2 — Directly From Hadith (Exact, Not Calibrated)

These are stated explicitly in the hadith and need no number-choosing:

| Value | Hadith Basis |
| :--- | :--- |
| Asr shadow ratio = 1:1 (or 2:1) | Explicit ("shadow equals height") |
| Maghrib start = sunset | Explicit |
| Fajr end = sunrise | Sahih Muslim 612a |
| Isha end = midnight (half night) | Sahih Muslim 612a |
| Tahajjud window = Isha → Fajr | Derived from night definition |
| Witr window = Isha → Fajr | Explicit |
| Forbidden after Fajr | Sahih al-Bukhari 586 |
| Forbidden after Asr | Same |
| Forbidden at zenith | Sahih Muslim 831 |
| Sunset-approach forbidden | Sahih Muslim 831 |

These are exact, and the boundaries are geometric (sun events), so no number is chosen.

## Tier 3 — Calibration Proxies (Like Fajr/Isha Angles)

These are **not calculable** and **not directly from hadith**. They are conventional values chosen by scholars or derived from observation:

| Parameter | Default | Hadith Says | Why It's a Proxy |
| :--- | :--- | :--- | :--- |
| `--fajr-angle` | −18.0° | "True dawn" | Hadith describes phenomenon, not degrees |
| `--isha-angle` | −17.0° | "Redness disappears" | Same |
| **`--spear-alt`** | **5.0°** | "Height of a spear" | Visual description; the 5° is a convention |
| **`--duha-alt`** | **15.0°** | "Heat of sand" | Visual description; the 15° is a convention |
| **`--yellow-alt`** | **4.0°** | "Sun turns yellow" | Visual description; the 4° is a convention |
| **`--zenith-before`** | **15 min** | "When sun is at its height" | Duration not specified; precautionary |
| **`--zenith-after`** | **0 min** | Same | Same |
| **`--asr-early-min`** | **60 min** | "Pray Asr early" | Duration not specified; convention |

**All five bolded parameters are proxies, exactly like the Fajr/Isha angles.** They cannot be computed. They are chosen.

## Which Tiers Affect Which Outputs

| Output | Depends On |
| :--- | :--- |
| **Fajr time** | `--fajr-angle` (proxy) + Tier 1 calculation |
| **Isha time** | `--isha-angle` (proxy) + Tier 1 calculation |
| **Sunrise, Sunset** | Tier 1 only (no proxy) |
| **Dhuhr** | Tier 1 only |
| **Asr** | Tier 1 + hadith ratio (Tier 2) |
| **Maghrib** | Tier 1 only |
| **Tahajjud, Witr** | Tier 1 + hadith fractions |
| **Ishraq window start** | `--spear-alt` (proxy) |
| **Duha best time** | `--duha-alt` (proxy) |
| **Forbidden zenith window** | `--zenith-before` / `--zenith-after` (proxies) |
| **Forbidden sunset window** | `--yellow-alt` (proxy) |
| **Asr best time window** | `--asr-early-min` (proxy) |

The five obligatory prayers (Fajr, Dhuhr, Asr, Maghrib, Isha) depend only on **two** proxies: `--fajr-angle` and `--isha-angle`. Everything else about them is Tier 1 or Tier 2.

The **voluntary prayers and forbidden intervals** depend on **five additional** proxies that you currently accept as defaults.

## Why This Matters

If you ship the CLI to a user and say *"only Fajr and Isha angles are calibrated,"* you are misleading them. When they see:

```
Ishraq      6:01 AM → 12:43 PM
Duha        6:01 AM → 12:43 PM    best: 6:58 AM → 12:38 PM
```

They should know that the **6:01 AM start** is a consequence of `--spear-alt 5.0`, not a computed astronomical fact. Change `--spear-alt` to 4.0° and the Ishraq window will open earlier. Change it to 6.0° and it opens later. The value is a convention, not a calculation.

Same for `--duha-alt`, `--yellow-alt`, `--zenith-before`, `--asr-early-min`. All five are choices.

## The Clean Statement

The correct summary is:

> **Two proxies (Fajr/Isha angles) affect the five obligatory prayers.**
> **Five additional proxies (spear-alt, duha-alt, yellow-alt, zenith-before, zenith-after, asr-early-min) affect the voluntary-prayer windows, the best-time recommendations, and the forbidden intervals.**
> **Everything else — solar position, sunrise, sunset, solar noon, night fractions, Asr shadow-ratio time — is computed exactly from astronomy and hadith.**

So no, it is not just `--fajr-angle` and `--isha-angle`. You have **seven calibration parameters** in total, of which two affect the core prayer times and five affect the surrounding framework.

If you want to reduce the calibration surface, you can:

1. **Remove `--zenith-before`/`--zenith-after`** by hardcoding `15/0` (a fixed convention) — reduces user-facing parameters.
2. **Remove `--asr-early-min`** by hardcoding `60` — same.
3. **Remove `--spear-alt`, `--duha-alt`, `--yellow-alt`** by fixing them at conventional values and documenting them as "based on the scholar's interpretation of the visual description."

But you cannot eliminate them — they represent real interpretive decisions that the hadith leave open.

# Three Files — 7 Required Args (Regular), 5 Required (PCD/SPA)

Design decisions applied:

- **Regular-cli** required: `--lat --lon --tz --date --fajr-angle --isha-angle --asr-ratio` (7)
- **pcd-cli / spa-cli** required: `--lat --lon --tz --date --asr-ratio` (5); `--fajr-angle` / `--isha-angle` remain optional overrides
- Hardcoded constants: `SPEAR_ALT = 5.0`, `DUHA_ALT = 15.0`, `YELLOW_ALT = 4.0`, `ZENITH_BEFORE = 15.0`, `ZENITH_AFTER = 0.0`
- `--asr-early-fraction` (default 0.33) replaces `--asr-early-min`
- `--elev` optional, default 0

The `--asr-early-fraction` scales with the Asr preferred window:

```python
T_asr_early_end = T_asr + asr_early_fraction * (T_yellow - T_asr)
```

For Dhaka in September, the window is ~141 min, so 0.33 → best time ends ~46 min after Asr opens.

---

## 1. `prayer-times-regular-cli.py`

```python
#!/usr/bin/env python3
"""
Hadith-Based Islamic Prayer Time Calculator (CLI) — v19 REGULAR
---------------------------------------------------------------
7 required args: --lat --lon --tz --date --fajr-angle --isha-angle --asr-ratio
Five convention constants hardcoded. Optional: --elev, --asr-early-fraction.

Usage:
  python prayer-times-regular-cli.py \
    --lat 23.836468 --lon 90.3695392 --tz Asia/Dhaka --date 2026-09-16 \
    --fajr-angle 18.0 --isha-angle 17.0 --asr-ratio 1.0
"""

VERSION = "v19 REGULAR"
DHUHR_OFFSET_MINUTES = 2.5

# --- Hardcoded convention constants (documented defaults) ---
SPEAR_ALT      = 5.0   # "height of a spear"  → Ishraq window opens
DUHA_ALT       = 15.0  # "heat of sand"        → Duha best time begins
YELLOW_ALT     = 4.0   # "sun turns yellow"    → sunset-approach forbidden
ZENITH_BEFORE  = 15.0  # minutes before Istiwa' for zenith precaution
ZENITH_AFTER   = 0.0   # minutes after Istiwa' before Dhuhr opens

import argparse
import math
import sys
from datetime import datetime, date as date_cls

try:
    from zoneinfo import ZoneInfo
except ImportError:
    ZoneInfo = None

# ============================================================
# ASTRONOMY
# ============================================================

def julian_day(y, m, d):
    if m <= 2:
        y -= 1
        m += 12
    A = y // 100
    B = 2 - A + A // 4
    return int(365.25 * (y + 4716)) + int(30.6001 * (m + 1)) + d + B - 1524.5

def solar_position(jd):
    n = jd - 2451545.0
    L = (280.460 + 0.9856474 * n) % 360
    g = math.radians((357.528 + 0.9856003 * n) % 360)
    lam = math.radians(L + 1.915 * math.sin(g) + 0.020 * math.sin(2 * g))
    eps = math.radians(23.439 - 0.0000004 * n)
    decl = math.degrees(math.asin(math.sin(eps) * math.sin(lam)))
    RA = math.degrees(math.atan2(math.cos(eps) * math.sin(lam), math.cos(lam)))
    EoT = L - RA
    if EoT > 180:  EoT -= 360
    if EoT < -180: EoT += 360
    return decl, EoT

def hour_angle(alt_deg, lat_deg, decl_deg):
    alt, lat, dec = map(math.radians, (alt_deg, lat_deg, decl_deg))
    denom = math.cos(lat) * math.cos(dec)
    if abs(denom) < 1e-12:
        return None
    c = (math.sin(alt) - math.sin(lat) * math.sin(dec)) / denom
    if c > 1 or c < -1:
        return None
    return math.degrees(math.acos(c))

def asr_altitude(lat_deg, decl_deg, ratio=1.0):
    noon_alt = 90.0 - abs(lat_deg - decl_deg)
    if noon_alt <= 0:
        return None
    cot_noon = 1.0 / math.tan(math.radians(noon_alt))
    return math.degrees(math.atan(1.0 / (ratio + cot_noon)))

# ============================================================
# FORMATTING
# ============================================================

def fmt_ampm(h):
    if h is None:
        return "--:-- --"
    h %= 24
    hh = int(h)
    mm = int(round((h - hh) * 60))
    if mm == 60:
        hh = (hh + 1) % 24
        mm = 0
    return f"{hh % 12 or 12}:{mm:02d} {'AM' if hh < 12 else 'PM'}"

def span(a, b):
    if a is None and b is None:
        return "—"
    if a is None:
        return f"until {fmt_ampm(b)}"
    if b is None:
        return f"from {fmt_ampm(a)}"
    if abs(a - b) < 1 / 120:
        return fmt_ampm(a)
    return f"{fmt_ampm(a)} → {fmt_ampm(b)}"

# ============================================================
# CALCULATION
# ============================================================

def calculate(y, m, d, lat, lon, tz, fajr_angle, isha_angle, asr_ratio,
              asr_early_fraction):
    jd = julian_day(y, m, d)
    decl, EoT = solar_position(jd)
    noon = 12.0 - lon / 15.0 - EoT / 15.0 + tz

    def before(alt):
        a = hour_angle(alt, lat, decl)
        return noon - a / 15.0 if a is not None else None

    def after(alt):
        a = hour_angle(alt, lat, decl)
        return noon + a / 15.0 if a is not None else None

    T_fajr    = before(-fajr_angle)
    T_sunrise = before(-0.833)
    T_spear   = before(SPEAR_ALT)
    T_duha    = before(DUHA_ALT)
    T_asr     = after(asr_altitude(lat, decl, asr_ratio))
    T_yellow  = after(YELLOW_ALT)
    T_maghrib = after(-0.833)
    T_isha    = after(-isha_angle)

    T_istiwa = noon
    T_zawal  = noon
    T_zenith_start = T_istiwa - ZENITH_BEFORE / 60.0
    T_zenith_end   = T_istiwa + ZENITH_AFTER  / 60.0
    T_dhuhr = T_zawal + DHUHR_OFFSET_MINUTES / 60.0

    if T_sunrise is None or T_spear is None:
        sys.exit("[FATAL] sunrise or spear is None (polar geometry?)")
    if T_sunrise >= T_spear:
        sys.exit("[FATAL] sunrise >= spear")

    # Asr early best-time end: fraction of the preferred window (Asr → yellow)
    T_asr_early_end = (T_asr + asr_early_fraction * (T_yellow - T_asr)) \
        if (T_asr is not None and T_yellow is not None) else None

    if T_maghrib is not None and T_fajr is not None:
        night_len = (T_fajr + 24.0) - T_maghrib
        T_midnight   = T_maghrib + night_len / 2.0
        T_last_third = T_maghrib + (2.0 / 3.0) * night_len
    else:
        T_midnight = T_last_third = None

    T_duha_best_end   = T_zenith_start - 5.0 / 60.0
    T_isha_best_start = (T_isha + T_midnight) / 2.0 if (T_isha and T_midnight) else None

    return {
        "fajr": T_fajr, "sunrise": T_sunrise, "spear": T_spear,
        "duha_warm": T_duha, "istiwa": T_istiwa, "zawal": T_zawal,
        "dhuhr": T_dhuhr, "asr": T_asr, "yellow": T_yellow,
        "asr_early_end": T_asr_early_end, "maghrib": T_maghrib, "isha": T_isha,
        "midnight": T_midnight, "last_third": T_last_third,
        "zenith_start": T_zenith_start, "zenith_end": T_zenith_end,
        "duha_best_start": T_duha, "duha_best_end": T_duha_best_end,
        "isha_best_start": T_isha_best_start,
    }

# ============================================================
# OUTPUT
# ============================================================

def print_report(r, a, tz_label):
    line = "=" * 84
    print(f"\n{line}")
    print(f"  HADITH-BASED PRAYER TIMES  —  {VERSION}")
    print(f"{line}")
    print(f"  Date       : {a.date}")
    print(f"  Location   : {a.lat:.4f}°, {a.lon:.4f}°   Elev: {a.elev} m")
    print(f"  Timezone   : {tz_label}  (UTC{a.tz_offset:+.1f})")
    print(f"  Required   : Fajr={a.fajr_angle}°  Isha={a.isha_angle}°  "
          f"AsrRatio={a.asr_ratio}")
    print(f"  Conventions: Spear={SPEAR_ALT}°  Duha={DUHA_ALT}°  "
          f"Yellow={YELLOW_ALT}°  ZenithBefore={ZENITH_BEFORE}min  "
          f"ZenithAfter={ZENITH_AFTER}min  "
          f"AsrEarlyFraction={a.asr_early_fraction}")

    print(f"\n  PRAYER WINDOWS  (chronological, forbidden intervals between)")
    print("  " + "-" * 82)
    print(f"  {'':<12}{'WINDOW':<34}{'BEST TIME':<32}")
    print("  " + "-" * 82)

    def prow(name, win, best):
        w = span(*win) if win else "—"
        b = best if best else ""
        print(f"  {name:<12}{w:<34}{b:<32}")

    prow("Fajr", (r["fajr"], r["sunrise"]), f"best: {fmt_ampm(r['fajr'])}")
    prow("Forbidden", (r["sunrise"], r["spear"]), "(nafl — after Fajr until spear height)")
    prow("Ishraq", (r["spear"], r["zenith_start"]), f"best: {fmt_ampm(r['spear'])}")
    prow("Duha", (r["spear"], r["zenith_start"]), f"best: {span(r['duha_best_start'], r['duha_best_end'])}")
    prow("Forbidden", (r["zenith_start"], r["zenith_end"]), "(nafl — zenith)")
    prow("Dhuhr", (r["dhuhr"], r["asr"]), f"best: {fmt_ampm(r['dhuhr'])}")
    prow("Asr", (r["asr"], r["yellow"]), f"best: {span(r['asr'], r['asr_early_end'])} (pray early)")
    prow("Forbidden", (r["yellow"], r["maghrib"]), "(all prayer — sunset approach)")
    prow("Maghrib", (r["maghrib"], r["isha"]), f"best: {fmt_ampm(r['maghrib'])}")
    prow("Isha", (r["isha"], r["midnight"]), f"best: {span(r['isha_best_start'], r['midnight'])}")
    prow("Tahajjud", (r["isha"], r["fajr"]), f"best: {span(r['last_third'], r['fajr'])}")
    prow("Witr", (r["isha"], r["fajr"]), f"best: {span(r['last_third'], r['fajr'])}")

    print(f"\n  SOLAR NOON ANCHORS")
    print("  " + "-" * 82)
    print(f"  Istiwa' — sun at zenith (peak)              : {fmt_ampm(r['istiwa'])}")
    print(f"  Zawal   — sun begins decline                : {fmt_ampm(r['zawal'])}")
    print(f"  Dhuhr opens (Zawal + {DHUHR_OFFSET_MINUTES} min)         : {fmt_ampm(r['dhuhr'])}")
    print(f"  Zenith precaution begins                    : {fmt_ampm(r['zenith_start'])}")
    print(f"  Zenith precaution ends                      : {fmt_ampm(r['zenith_end'])}")
    print(f"\n{line}\n")

# ============================================================
# CLI
# ============================================================

def parse_tz(tz_str, for_date):
    try:
        off = float(tz_str)
        return off, f"UTC{off:+.1f}"
    except ValueError:
        pass
    if ZoneInfo is not None:
        try:
            zone = ZoneInfo(tz_str)
            probe = datetime(for_date.year, for_date.month, for_date.day,
                             12, 0, 0, tzinfo=zone)
            off = probe.utcoffset().total_seconds() / 3600.0
            return off, tz_str
        except Exception:
            pass
    sys.exit(f"[FATAL] cannot interpret timezone '{tz_str}'")

def main():
    p = argparse.ArgumentParser(
        description="Hadith-based prayer time calculator (fixed angles). "
                    "Angles are POSITIVE depression (degrees below horizon).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--lat", type=float, required=True)
    p.add_argument("--lon", type=float, required=True)
    p.add_argument("--tz", type=str, required=True,
                   help="Numeric offset (+6) or IANA name (Asia/Dhaka)")
    p.add_argument("--date", type=str, required=True, help="YYYY-MM-DD")
    p.add_argument("--fajr-angle", type=float, required=True,
                   help="Fajr solar DEPRESSION in degrees (positive). Common: 18.0")
    p.add_argument("--isha-angle", type=float, required=True,
                   help="Isha solar DEPRESSION in degrees (positive). Common: 17.0")
    p.add_argument("--asr-ratio", type=float, required=True, choices=[1.0, 2.0],
                   help="Asr shadow ratio: 1.0 (standard) or 2.0 (Hanafi)")

    p.add_argument("--elev", type=float, default=0.0,
                   help="Elevation in metres (optional, default 0)")
    p.add_argument("--asr-early-fraction", type=float, default=0.33,
                   help="Fraction of the Asr preferred window considered "
                        "'best' (default 0.33). 0.0 = only the opening moment; "
                        "1.0 = the entire window until sun-yellowing.")

    a = p.parse_args()

    if a.fajr_angle <= 0 or a.fajr_angle >= 90:
        sys.exit("Error: --fajr-angle must be POSITIVE (0 < x < 90). Example: 18.0")
    if a.isha_angle <= 0 or a.isha_angle >= 90:
        sys.exit("Error: --isha-angle must be POSITIVE (0 < x < 90). Example: 17.0")
    if not (0.0 <= a.asr_early_fraction <= 1.0):
        sys.exit("Error: --asr-early-fraction must be between 0 and 1.")

    try:
        d = datetime.strptime(a.date, "%Y-%m-%d").date()
    except ValueError:
        sys.exit("--date must be YYYY-MM-DD")

    a.tz_offset, tz_label = parse_tz(a.tz, d)

    r = calculate(
        d.year, d.month, d.day, a.lat, a.lon, a.tz_offset,
        a.fajr_angle, a.isha_angle, a.asr_ratio, a.asr_early_fraction,
    )
    print_report(r, a, tz_label)

if __name__ == "__main__":
    main()
```

**Run for Dhaka:**

```bash
python prayer-times-regular-cli.py \
  --lat 23.836468 --lon 90.3695392 --tz Asia/Dhaka --date 2026-09-16 \
  --fajr-angle 18.0 --isha-angle 17.0 --asr-ratio 1.0
```

---

## 2. `prayer-times-pcd-cli.py`

```python
#!/usr/bin/env python3
"""
Hadith-Based Islamic Prayer Time Calculator (CLI) — v19 PCD
-----------------------------------------------------------
5 required args: --lat --lon --tz --date --asr-ratio
PCD computes Fajr/Isha angles. Optional overrides via --fajr-angle/--isha-angle.
Five convention constants hardcoded.

Usage:
  python prayer-times-pcd-cli.py \
    --lat 23.836468 --lon 90.3695392 --tz Asia/Dhaka --date 2026-09-16 \
    --asr-ratio 1.0
"""

VERSION = "v19 PCD"
DHUHR_OFFSET_MINUTES = 2.5

SPEAR_ALT      = 5.0
DUHA_ALT       = 15.0
YELLOW_ALT     = 4.0
ZENITH_BEFORE  = 15.0
ZENITH_AFTER   = 0.0

import argparse
import math
import sys
from datetime import datetime, date as date_cls, timezone

try:
    from zoneinfo import ZoneInfo
except ImportError:
    ZoneInfo = None

# ============================================================
# PCD ALGORITHM
# ============================================================

LAT_SCALE = 55.0
ANGLE_MIN = 10.0
ANGLE_MAX = 22.0
DEG = math.pi / 180.0

def _to_julian_date(d):
    dt = datetime(d.year, d.month, d.day, tzinfo=timezone.utc)
    return dt.timestamp() / 86400.0 + 2440587.5

def _solar_ephemeris(jd):
    T = (jd - 2451545.0) / 36525.0
    L0 = ((280.46646 + 36000.76983 * T + 0.0003032 * T * T) % 360 + 360) % 360
    M = ((357.52911 + 35999.05029 * T - 0.0001537 * T * T) % 360 + 360) % 360
    Mrad = M * DEG
    e = 0.016708634 - 0.000042037 * T - 0.0000001267 * T * T
    C = ((1.914602 - 0.004817 * T - 0.000014 * T * T) * math.sin(Mrad) +
         (0.019993 - 0.000101 * T) * math.sin(2 * Mrad) + 0.000289 * math.sin(3 * Mrad))
    sunLon = L0 + C
    nu = M + C
    nuRad = nu * DEG
    r = (1.000001018 * (1 - e * e)) / (1 + e * math.cos(nuRad))
    Omega = ((125.04 - 1934.136 * T) % 360 + 360) % 360
    OmegaRad = Omega * DEG
    lam = sunLon - 0.00569 - 0.00478 * math.sin(OmegaRad)
    lamRad = lam * DEG
    eps0 = (23.0 + 26.0 / 60.0 + 21.448 / 3600.0
            - (46.8150 * T + 0.00059 * T * T - 0.001813 * T * T * T) / 3600.0)
    eps = eps0 + 0.00256 * math.cos(OmegaRad)
    decl = math.asin(math.sin(eps * DEG) * math.sin(lamRad)) / DEG
    eclLon = lamRad % (2 * math.pi)
    return decl, r, eclLon

def _atmospheric_refraction(altitude_deg, pressure_mbar=1013.25, temperature_c=15.0):
    h = altitude_deg
    if h < -1.0 or h > 90.0:
        return 0.0
    denom = math.tan((h + 10.3 / (h + 5.11)) * DEG)
    if denom == 0:
        return 0.0
    R_arcmin = 1.02 / denom
    R_arcmin *= (pressure_mbar / 1010.0) * (283.0 / (273.0 + temperature_c))
    return R_arcmin / 60.0

def _is_leap(year):
    return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)

def _compute_dyy(d, latitude):
    year = d.year
    days_in_year = 366 if _is_leap(year) else 365
    ref_month = 12 if latitude >= 0 else 6
    ref = date_cls(year, ref_month, 21)
    diff = (d - ref).days
    if diff < 0:
        diff += days_in_year
    return diff, days_in_year

def _interpolate_segment(dyy, days_in_year, a, b, c, d):
    if dyy < 91:   return a + ((b - a) / 91) * dyy
    if dyy < 137:  return b + ((c - b) / 46) * (dyy - 91)
    if dyy < 183:  return c + ((d - c) / 46) * (dyy - 137)
    if dyy < 229:  return d + ((c - d) / 46) * (dyy - 183)
    if dyy < 275:  return c + ((b - c) / 46) * (dyy - 229)
    length = days_in_year - 275
    return b + ((a - b) / length) * (dyy - 275)

def _get_msc_fajr(d, latitude):
    lat_abs = abs(latitude)
    dyy, days_in_year = _compute_dyy(d, latitude)
    BASE = 75.0
    a = BASE + (28.65 / LAT_SCALE) * lat_abs
    b = BASE + (19.44 / LAT_SCALE) * lat_abs
    c = BASE + (32.74 / LAT_SCALE) * lat_abs
    d_ = BASE + (48.10 / LAT_SCALE) * lat_abs
    return round(_interpolate_segment(dyy, days_in_year, a, b, c, d_))

def _get_msc_isha(d, latitude, shafaq="general"):
    lat_abs = abs(latitude)
    dyy, days_in_year = _compute_dyy(d, latitude)
    if shafaq == "ahmer":
        BASE = 62.0
        a = BASE + (17.40 / LAT_SCALE) * lat_abs
        b = BASE - (7.16 / LAT_SCALE) * lat_abs
        c = BASE + (5.12 / LAT_SCALE) * lat_abs
        d_ = BASE + (19.44 / LAT_SCALE) * lat_abs
    elif shafaq == "abyad":
        BASE = 75.0
        a = BASE + (25.60 / LAT_SCALE) * lat_abs
        b = BASE + (7.16 / LAT_SCALE) * lat_abs
        c = BASE + (36.84 / LAT_SCALE) * lat_abs
        d_ = BASE + (81.84 / LAT_SCALE) * lat_abs
    else:
        BASE = 75.0
        a = BASE + (25.60 / LAT_SCALE) * lat_abs
        b = BASE + (2.05 / LAT_SCALE) * lat_abs
        c = BASE - (9.21 / LAT_SCALE) * lat_abs
        d_ = BASE + (6.14 / LAT_SCALE) * lat_abs
    return round(_interpolate_segment(dyy, days_in_year, a, b, c, d_))

def _minutes_to_depression(minutes, lat_deg, decl_deg):
    phi = lat_deg * DEG
    delta = decl_deg * DEG
    cos_phi = math.cos(phi); sin_phi = math.sin(phi)
    cos_delta = math.cos(delta); sin_delta = math.sin(delta)
    h0 = -0.833 * DEG
    sin_h0 = math.sin(h0)
    denom = cos_phi * cos_delta
    if abs(denom) < 1e-10: return float("nan")
    cos_h_rise = (sin_h0 - sin_phi * sin_delta) / denom
    if cos_h_rise < -1 or cos_h_rise > 1: return float("nan")
    H_rise = math.acos(cos_h_rise)
    delta_H = (minutes / 60.0) * 15.0 * DEG
    H_prayer = H_rise + delta_H
    if H_prayer > math.pi:
        sin_h_mid = sin_phi * sin_delta + cos_phi * cos_delta * math.cos(math.pi)
        h_mid = math.asin(max(-1.0, min(1.0, sin_h_mid)))
        return -h_mid / DEG
    sin_h = sin_phi * sin_delta + cos_phi * cos_delta * math.cos(H_prayer)
    h = math.asin(max(-1.0, min(1.0, sin_h)))
    return -h / DEG

def _earth_sun_distance_correction(r):
    return -0.5 * math.log(r)

def _fourier_smoothing_correction(ecl_lon, lat_abs_deg):
    theta = ecl_lon; phi = lat_abs_deg * DEG
    return (0.03 * math.sin(theta) - 0.05 * math.cos(theta)
            + 0.02 * math.sin(2 * theta) + 0.02 * math.cos(2 * theta)
            - 0.008 * phi * math.sin(theta) + 0.004 * phi * math.cos(theta))

def _clip(v, lo, hi):
    return max(lo, min(hi, v))

def _round3(v):
    return round(v, 3)

def get_pcd_angles(d, lat, lng=0.0, elevation=0.0,
                   temperature=15.0, pressure=1013.25, shafaq="general"):
    jd = _to_julian_date(d)
    decl, r, ecl_lon = _solar_ephemeris(jd)
    msc_fajr_min = _get_msc_fajr(d, lat)
    msc_isha_min = _get_msc_isha(d, lat, shafaq)
    fajr_base = _minutes_to_depression(msc_fajr_min, lat, decl)
    isha_base = _minutes_to_depression(msc_isha_min, lat, decl)
    if not math.isfinite(fajr_base): fajr_base = 18.0
    if not math.isfinite(isha_base): isha_base = 18.0
    r_corr = _earth_sun_distance_correction(r)
    fourier_corr = _fourier_smoothing_correction(ecl_lon, abs(lat))
    refr_fajr = _atmospheric_refraction(-(fajr_base + 0.5), pressure, temperature)
    refr_isha = _atmospheric_refraction(-(isha_base + 0.5), pressure, temperature)
    horizon_dip = 1.06 * math.sqrt(max(elevation, 0.0) / 1000.0)
    elev_corr = horizon_dip * 0.3
    raw_fajr = fajr_base + r_corr + fourier_corr + refr_fajr + elev_corr
    raw_isha = isha_base + r_corr + fourier_corr + refr_isha + elev_corr
    return (_round3(_clip(raw_fajr, ANGLE_MIN, ANGLE_MAX)),
            _round3(_clip(raw_isha, ANGLE_MIN, ANGLE_MAX)))

# ============================================================
# ASTRONOMY (Meeus) for other prayers
# ============================================================

def julian_day(y, m, d):
    if m <= 2: y -= 1; m += 12
    A = y // 100; B = 2 - A + A // 4
    return int(365.25 * (y + 4716)) + int(30.6001 * (m + 1)) + d + B - 1524.5

def solar_position(jd):
    n = jd - 2451545.0
    L = (280.460 + 0.9856474 * n) % 360
    g = math.radians((357.528 + 0.9856003 * n) % 360)
    lam = math.radians(L + 1.915 * math.sin(g) + 0.020 * math.sin(2 * g))
    eps = math.radians(23.439 - 0.0000004 * n)
    decl = math.degrees(math.asin(math.sin(eps) * math.sin(lam)))
    RA = math.degrees(math.atan2(math.cos(eps) * math.sin(lam), math.cos(lam)))
    EoT = L - RA
    if EoT > 180: EoT -= 360
    if EoT < -180: EoT += 360
    return decl, EoT

def hour_angle(alt_deg, lat_deg, decl_deg):
    alt, lat, dec = map(math.radians, (alt_deg, lat_deg, decl_deg))
    denom = math.cos(lat) * math.cos(dec)
    if abs(denom) < 1e-12: return None
    c = (math.sin(alt) - math.sin(lat) * math.sin(dec)) / denom
    if c > 1 or c < -1: return None
    return math.degrees(math.acos(c))

def asr_altitude(lat_deg, decl_deg, ratio=1.0):
    noon_alt = 90.0 - abs(lat_deg - decl_deg)
    if noon_alt <= 0: return None
    cot_noon = 1.0 / math.tan(math.radians(noon_alt))
    return math.degrees(math.atan(1.0 / (ratio + cot_noon)))

# ============================================================
# FORMATTING
# ============================================================

def fmt_ampm(h):
    if h is None: return "--:-- --"
    h %= 24
    hh = int(h); mm = int(round((h - hh) * 60))
    if mm == 60: hh = (hh + 1) % 24; mm = 0
    return f"{hh % 12 or 12}:{mm:02d} {'AM' if hh < 12 else 'PM'}"

def span(a, b):
    if a is None and b is None: return "—"
    if a is None: return f"until {fmt_ampm(b)}"
    if b is None: return f"from {fmt_ampm(a)}"
    if abs(a - b) < 1 / 120: return fmt_ampm(a)
    return f"{fmt_ampm(a)} → {fmt_ampm(b)}"

# ============================================================
# CALCULATION
# ============================================================

def calculate(y, m, d, lat, lon, tz, fajr_angle, isha_angle, asr_ratio,
              asr_early_fraction):
    jd = julian_day(y, m, d)
    decl, EoT = solar_position(jd)
    noon = 12.0 - lon / 15.0 - EoT / 15.0 + tz

    def before(alt):
        a = hour_angle(alt, lat, decl)
        return noon - a / 15.0 if a is not None else None

    def after(alt):
        a = hour_angle(alt, lat, decl)
        return noon + a / 15.0 if a is not None else None

    T_fajr    = before(-fajr_angle)
    T_sunrise = before(-0.833)
    T_spear   = before(SPEAR_ALT)
    T_duha    = before(DUHA_ALT)
    T_asr     = after(asr_altitude(lat, decl, asr_ratio))
    T_yellow  = after(YELLOW_ALT)
    T_maghrib = after(-0.833)
    T_isha    = after(-isha_angle)

    T_istiwa = noon
    T_zawal  = noon
    T_zenith_start = T_istiwa - ZENITH_BEFORE / 60.0
    T_zenith_end   = T_istiwa + ZENITH_AFTER  / 60.0
    T_dhuhr = T_zawal + DHUHR_OFFSET_MINUTES / 60.0

    if T_sunrise is None or T_spear is None:
        sys.exit("[FATAL] sunrise or spear is None")
    if T_sunrise >= T_spear:
        sys.exit("[FATAL] sunrise >= spear")

    T_asr_early_end = (T_asr + asr_early_fraction * (T_yellow - T_asr)) \
        if (T_asr is not None and T_yellow is not None) else None

    if T_maghrib is not None and T_fajr is not None:
        night_len = (T_fajr + 24.0) - T_maghrib
        T_midnight   = T_maghrib + night_len / 2.0
        T_last_third = T_maghrib + (2.0 / 3.0) * night_len
    else:
        T_midnight = T_last_third = None

    T_duha_best_end   = T_zenith_start - 5.0 / 60.0
    T_isha_best_start = (T_isha + T_midnight) / 2.0 if (T_isha and T_midnight) else None

    return {
        "fajr": T_fajr, "sunrise": T_sunrise, "spear": T_spear,
        "duha_warm": T_duha, "istiwa": T_istiwa, "zawal": T_zawal,
        "dhuhr": T_dhuhr, "asr": T_asr, "yellow": T_yellow,
        "asr_early_end": T_asr_early_end, "maghrib": T_maghrib, "isha": T_isha,
        "midnight": T_midnight, "last_third": T_last_third,
        "zenith_start": T_zenith_start, "zenith_end": T_zenith_end,
        "duha_best_start": T_duha, "duha_best_end": T_duha_best_end,
        "isha_best_start": T_isha_best_start,
    }

# ============================================================
# OUTPUT
# ============================================================

def print_report(r, a, tz_label, fajr_src, isha_src):
    line = "=" * 84
    print(f"\n{line}")
    print(f"  HADITH-BASED PRAYER TIMES  —  {VERSION}")
    print(f"{line}")
    print(f"  Date       : {a.date}")
    print(f"  Location   : {a.lat:.4f}°, {a.lon:.4f}°   Elev: {a.elev} m")
    print(f"  Timezone   : {tz_label}  (UTC{a.tz_offset:+.1f})")
    print(f"  Angles     : Fajr={r['fajr_angle']}° ({fajr_src})  "
          f"Isha={r['isha_angle']}° ({isha_src})")
    print(f"  Required   : AsrRatio={a.asr_ratio}")
    print(f"  Conventions: Spear={SPEAR_ALT}°  Duha={DUHA_ALT}°  "
          f"Yellow={YELLOW_ALT}°  ZenithBefore={ZENITH_BEFORE}min  "
          f"AsrEarlyFraction={a.asr_early_fraction}")

    print(f"\n  PRAYER WINDOWS  (chronological, forbidden intervals between)")
    print("  " + "-" * 82)
    print(f"  {'':<12}{'WINDOW':<34}{'BEST TIME':<32}")
    print("  " + "-" * 82)

    def prow(name, win, best):
        w = span(*win) if win else "—"
        b = best if best else ""
        print(f"  {name:<12}{w:<34}{b:<32}")

    prow("Fajr", (r["fajr"], r["sunrise"]), f"best: {fmt_ampm(r['fajr'])}")
    prow("Forbidden", (r["sunrise"], r["spear"]), "(nafl — after Fajr until spear height)")
    prow("Ishraq", (r["spear"], r["zenith_start"]), f"best: {fmt_ampm(r['spear'])}")
    prow("Duha", (r["spear"], r["zenith_start"]), f"best: {span(r['duha_best_start'], r['duha_best_end'])}")
    prow("Forbidden", (r["zenith_start"], r["zenith_end"]), "(nafl — zenith)")
    prow("Dhuhr", (r["dhuhr"], r["asr"]), f"best: {fmt_ampm(r['dhuhr'])}")
    prow("Asr", (r["asr"], r["yellow"]), f"best: {span(r['asr'], r['asr_early_end'])} (pray early)")
    prow("Forbidden", (r["yellow"], r["maghrib"]), "(all prayer — sunset approach)")
    prow("Maghrib", (r["maghrib"], r["isha"]), f"best: {fmt_ampm(r['maghrib'])}")
    prow("Isha", (r["isha"], r["midnight"]), f"best: {span(r['isha_best_start'], r['midnight'])}")
    prow("Tahajjud", (r["isha"], r["fajr"]), f"best: {span(r['last_third'], r['fajr'])}")
    prow("Witr", (r["isha"], r["fajr"]), f"best: {span(r['last_third'], r['fajr'])}")

    print(f"\n  SOLAR NOON ANCHORS")
    print("  " + "-" * 82)
    print(f"  Istiwa' — sun at zenith (peak)              : {fmt_ampm(r['istiwa'])}")
    print(f"  Zawal   — sun begins decline                : {fmt_ampm(r['zawal'])}")
    print(f"  Dhuhr opens (Zawal + {DHUHR_OFFSET_MINUTES} min)         : {fmt_ampm(r['dhuhr'])}")
    print(f"  Zenith precaution begins                    : {fmt_ampm(r['zenith_start'])}")
    print(f"  Zenith precaution ends                      : {fmt_ampm(r['zenith_end'])}")
    print(f"\n{line}\n")

# ============================================================
# CLI
# ============================================================

def parse_tz(tz_str, for_date):
    try:
        off = float(tz_str)
        return off, f"UTC{off:+.1f}"
    except ValueError:
        pass
    if ZoneInfo is not None:
        try:
            zone = ZoneInfo(tz_str)
            probe = datetime(for_date.year, for_date.month, for_date.day,
                             12, 0, 0, tzinfo=zone)
            return probe.utcoffset().total_seconds() / 3600.0, tz_str
        except Exception:
            pass
    sys.exit(f"[FATAL] cannot interpret timezone '{tz_str}'")

def main():
    p = argparse.ArgumentParser(
        description="Hadith-based prayer time calculator (PCD dynamic angles).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--lat", type=float, required=True)
    p.add_argument("--lon", type=float, required=True)
    p.add_argument("--tz", type=str, required=True)
    p.add_argument("--date", type=str, required=True, help="YYYY-MM-DD")
    p.add_argument("--asr-ratio", type=float, required=True, choices=[1.0, 2.0])

    p.add_argument("--elev", type=float, default=0.0)
    p.add_argument("--asr-early-fraction", type=float, default=0.33)

    # Optional PCD overrides
    p.add_argument("--fajr-angle", type=float, default=None,
                   help="Override PCD Fajr depression angle (positive degrees).")
    p.add_argument("--isha-angle", type=float, default=None,
                   help="Override PCD Isha depression angle (positive degrees).")
    p.add_argument("--temperature", type=float, default=15.0)
    p.add_argument("--pressure", type=float, default=1013.25)
    p.add_argument("--shafaq", type=str, default="general",
                   choices=["general", "ahmer", "abyad"])

    a = p.parse_args()

    if not (0.0 <= a.asr_early_fraction <= 1.0):
        sys.exit("Error: --asr-early-fraction must be between 0 and 1.")

    try:
        d = datetime.strptime(a.date, "%Y-%m-%d").date()
    except ValueError:
        sys.exit("--date must be YYYY-MM-DD")

    a.tz_offset, tz_label = parse_tz(a.tz, d)

    pcd_fajr, pcd_isha = get_pcd_angles(
        d, lat=a.lat, lng=a.lon, elevation=a.elev,
        temperature=a.temperature, pressure=a.pressure, shafaq=a.shafaq,
    )

    if a.fajr_angle is not None:
        fajr_angle, fajr_src = a.fajr_angle, "override"
    else:
        fajr_angle, fajr_src = pcd_fajr, "PCD"

    if a.isha_angle is not None:
        isha_angle, isha_src = a.isha_angle, "override"
    else:
        isha_angle, isha_src = pcd_isha, "PCD"

    r = calculate(
        d.year, d.month, d.day, a.lat, a.lon, a.tz_offset,
        fajr_angle, isha_angle, a.asr_ratio, a.asr_early_fraction,
    )
    r["fajr_angle"] = fajr_angle
    r["isha_angle"] = isha_angle
    print_report(r, a, tz_label, fajr_src, isha_src)

if __name__ == "__main__":
    main()
```

**Run for Dhaka:**

```bash
python prayer-times-pcd-cli.py \
  --lat 23.836468 --lon 90.3695392 --tz Asia/Dhaka --date 2026-09-16 \
  --asr-ratio 1.0
```

---

## 3. `prayer-times-spa-cli.py`

```python
#!/usr/bin/env python3
"""
Hadith-Based Islamic Prayer Time Calculator — v19 NREL SPA
----------------------------------------------------------
5 required args: --lat --lon --tz --date --asr-ratio
PCD angles + NREL SPA solar position. Optional Fajr/Isha overrides.

Requires: pip install pandas pytz pvlib
Usage:
  python prayer-times-spa-cli.py \
    --lat 23.836468 --lon 90.3695392 --tz Asia/Dhaka --date 2026-09-16 \
    --asr-ratio 1.0
"""

VERSION = "v19 NREL SPA"
DHUHR_OFFSET_MINUTES = 2.5

SPEAR_ALT      = 5.0
DUHA_ALT       = 15.0
YELLOW_ALT     = 4.0
ZENITH_BEFORE  = 15.0
ZENITH_AFTER   = 0.0

import argparse
import math
import sys
from datetime import datetime, date as date_cls, timezone

try:
    from zoneinfo import ZoneInfo
except ImportError:
    ZoneInfo = None

try:
    import pandas as pd
except Exception as e:
    sys.exit(f"[FATAL] pandas not installed: {e}\nRun: pip install pandas")

try:
    import pytz
except Exception as e:
    sys.exit(f"[FATAL] pytz not installed: {e}\nRun: pip install pytz")

try:
    from pvlib import solarposition
except Exception as e:
    sys.exit(f"[FATAL] pvlib not installed: {e}\nRun: pip install pvlib")

# ============================================================
# PCD ALGORITHM (inlined — identical to pcd-cli)
# ============================================================

LAT_SCALE = 55.0
ANGLE_MIN = 10.0
ANGLE_MAX = 22.0
DEG = math.pi / 180.0

def _to_julian_date(d):
    dt = datetime(d.year, d.month, d.day, tzinfo=timezone.utc)
    return dt.timestamp() / 86400.0 + 2440587.5

def _solar_ephemeris(jd):
    T = (jd - 2451545.0) / 36525.0
    L0 = ((280.46646 + 36000.76983 * T + 0.0003032 * T * T) % 360 + 360) % 360
    M = ((357.52911 + 35999.05029 * T - 0.0001537 * T * T) % 360 + 360) % 360
    Mrad = M * DEG
    e = 0.016708634 - 0.000042037 * T - 0.0000001267 * T * T
    C = ((1.914602 - 0.004817 * T - 0.000014 * T * T) * math.sin(Mrad) +
         (0.019993 - 0.000101 * T) * math.sin(2 * Mrad) + 0.000289 * math.sin(3 * Mrad))
    sunLon = L0 + C
    nu = M + C
    nuRad = nu * DEG
    r = (1.000001018 * (1 - e * e)) / (1 + e * math.cos(nuRad))
    Omega = ((125.04 - 1934.136 * T) % 360 + 360) % 360
    OmegaRad = Omega * DEG
    lam = sunLon - 0.00569 - 0.00478 * math.sin(OmegaRad)
    lamRad = lam * DEG
    eps0 = (23.0 + 26.0 / 60.0 + 21.448 / 3600.0
            - (46.8150 * T + 0.00059 * T * T - 0.001813 * T * T * T) / 3600.0)
    eps = eps0 + 0.00256 * math.cos(OmegaRad)
    decl = math.asin(math.sin(eps * DEG) * math.sin(lamRad)) / DEG
    eclLon = lamRad % (2 * math.pi)
    return decl, r, eclLon

def _atmospheric_refraction(altitude_deg, pressure_mbar=1013.25, temperature_c=15.0):
    h = altitude_deg
    if h < -1.0 or h > 90.0:
        return 0.0
    denom = math.tan((h + 10.3 / (h + 5.11)) * DEG)
    if denom == 0:
        return 0.0
    R_arcmin = 1.02 / denom
    R_arcmin *= (pressure_mbar / 1010.0) * (283.0 / (273.0 + temperature_c))
    return R_arcmin / 60.0

def _is_leap(year):
    return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)

def _compute_dyy(d, latitude):
    year = d.year
    days_in_year = 366 if _is_leap(year) else 365
    ref_month = 12 if latitude >= 0 else 6
    ref = date_cls(year, ref_month, 21)
    diff = (d - ref).days
    if diff < 0: diff += days_in_year
    return diff, days_in_year

def _interpolate_segment(dyy, days_in_year, a, b, c, d):
    if dyy < 91:   return a + ((b - a) / 91) * dyy
    if dyy < 137:  return b + ((c - b) / 46) * (dyy - 91)
    if dyy < 183:  return c + ((d - c) / 46) * (dyy - 137)
    if dyy < 229:  return d + ((c - d) / 46) * (dyy - 183)
    if dyy < 275:  return c + ((b - c) / 46) * (dyy - 229)
    length = days_in_year - 275
    return b + ((a - b) / length) * (dyy - 275)

def _get_msc_fajr(d, latitude):
    lat_abs = abs(latitude)
    dyy, days_in_year = _compute_dyy(d, latitude)
    BASE = 75.0
    a = BASE + (28.65 / LAT_SCALE) * lat_abs
    b = BASE + (19.44 / LAT_SCALE) * lat_abs
    c = BASE + (32.74 / LAT_SCALE) * lat_abs
    d_ = BASE + (48.10 / LAT_SCALE) * lat_abs
    return round(_interpolate_segment(dyy, days_in_year, a, b, c, d_))

def _get_msc_isha(d, latitude, shafaq="general"):
    lat_abs = abs(latitude)
    dyy, days_in_year = _compute_dyy(d, latitude)
    if shafaq == "ahmer":
        BASE = 62.0
        a = BASE + (17.40 / LAT_SCALE) * lat_abs
        b = BASE - (7.16 / LAT_SCALE) * lat_abs
        c = BASE + (5.12 / LAT_SCALE) * lat_abs
        d_ = BASE + (19.44 / LAT_SCALE) * lat_abs
    elif shafaq == "abyad":
        BASE = 75.0
        a = BASE + (25.60 / LAT_SCALE) * lat_abs
        b = BASE + (7.16 / LAT_SCALE) * lat_abs
        c = BASE + (36.84 / LAT_SCALE) * lat_abs
        d_ = BASE + (81.84 / LAT_SCALE) * lat_abs
    else:
        BASE = 75.0
        a = BASE + (25.60 / LAT_SCALE) * lat_abs
        b = BASE + (2.05 / LAT_SCALE) * lat_abs
        c = BASE - (9.21 / LAT_SCALE) * lat_abs
        d_ = BASE + (6.14 / LAT_SCALE) * lat_abs
    return round(_interpolate_segment(dyy, days_in_year, a, b, c, d_))

def _minutes_to_depression(minutes, lat_deg, decl_deg):
    phi = lat_deg * DEG; delta = decl_deg * DEG
    cos_phi = math.cos(phi); sin_phi = math.sin(phi)
    cos_delta = math.cos(delta); sin_delta = math.sin(delta)
    h0 = -0.833 * DEG; sin_h0 = math.sin(h0)
    denom = cos_phi * cos_delta
    if abs(denom) < 1e-10: return float("nan")
    cos_h_rise = (sin_h0 - sin_phi * sin_delta) / denom
    if cos_h_rise < -1 or cos_h_rise > 1: return float("nan")
    H_rise = math.acos(cos_h_rise)
    delta_H = (minutes / 60.0) * 15.0 * DEG
    H_prayer = H_rise + delta_H
    if H_prayer > math.pi:
        sin_h_mid = sin_phi * sin_delta + cos_phi * cos_delta * math.cos(math.pi)
        h_mid = math.asin(max(-1.0, min(1.0, sin_h_mid)))
        return -h_mid / DEG
    sin_h = sin_phi * sin_delta + cos_phi * cos_delta * math.cos(H_prayer)
    h = math.asin(max(-1.0, min(1.0, sin_h)))
    return -h / DEG

def _earth_sun_distance_correction(r):
    return -0.5 * math.log(r)

def _fourier_smoothing_correction(ecl_lon, lat_abs_deg):
    theta = ecl_lon; phi = lat_abs_deg * DEG
    return (0.03 * math.sin(theta) - 0.05 * math.cos(theta)
            + 0.02 * math.sin(2 * theta) + 0.02 * math.cos(2 * theta)
            - 0.008 * phi * math.sin(theta) + 0.004 * phi * math.cos(theta))

def _clip(v, lo, hi):
    return max(lo, min(hi, v))

def _round3(v):
    return round(v, 3)

def get_pcd_angles(d, lat, lng=0.0, elevation=0.0,
                   temperature=15.0, pressure=1013.25, shafaq="general"):
    jd = _to_julian_date(d)
    decl, r, ecl_lon = _solar_ephemeris(jd)
    msc_fajr_min = _get_msc_fajr(d, lat)
    msc_isha_min = _get_msc_isha(d, lat, shafaq)
    fajr_base = _minutes_to_depression(msc_fajr_min, lat, decl)
    isha_base = _minutes_to_depression(msc_isha_min, lat, decl)
    if not math.isfinite(fajr_base): fajr_base = 18.0
    if not math.isfinite(isha_base): isha_base = 18.0
    r_corr = _earth_sun_distance_correction(r)
    fourier_corr = _fourier_smoothing_correction(ecl_lon, abs(lat))
    refr_fajr = _atmospheric_refraction(-(fajr_base + 0.5), pressure, temperature)
    refr_isha = _atmospheric_refraction(-(isha_base + 0.5), pressure, temperature)
    horizon_dip = 1.06 * math.sqrt(max(elevation, 0.0) / 1000.0)
    elev_corr = horizon_dip * 0.3
    raw_fajr = fajr_base + r_corr + fourier_corr + refr_fajr + elev_corr
    raw_isha = isha_base + r_corr + fourier_corr + refr_isha + elev_corr
    return (_round3(_clip(raw_fajr, ANGLE_MIN, ANGLE_MAX)),
            _round3(_clip(raw_isha, ANGLE_MIN, ANGLE_MAX)))

# ============================================================
# NREL SPA solar position
# ============================================================

def solar_position_spa(date, lat, lon, tz_offset,
                       elevation=0.0, temperature=15.0, pressure_mbar=1013.25):
    local_tz = pytz.FixedOffset(int(round(tz_offset * 60)))
    noon_local = pd.Timestamp(
        year=date.year, month=date.month, day=date.day,
        hour=12, minute=0, second=0, tzinfo=local_tz,
    )
    times = pd.DatetimeIndex([noon_local])
    spa = solarposition.get_solarposition(
        times, latitude=lat, longitude=lon, altitude=elevation,
        pressure=pressure_mbar * 100.0, temperature=temperature,
        method='nrel_numpy',
    )
    h_deg = float(spa['apparent_elevation'].iloc[0])
    az_deg = float(spa['azimuth'].iloc[0])
    phi = math.radians(lat); h = math.radians(h_deg); A = math.radians(az_deg)
    sin_decl = math.sin(h) * math.sin(phi) + math.cos(h) * math.cos(phi) * math.cos(A)
    sin_decl = max(-1.0, min(1.0, sin_decl))
    decl_deg = math.degrees(math.asin(sin_decl))
    eot_min = float(spa['equation_of_time'].iloc[0])
    return decl_deg, eot_min * 0.25

# ============================================================
# Hour-angle solver
# ============================================================

def hour_angle(alt_deg, lat_deg, decl_deg):
    alt, lat, dec = map(math.radians, (alt_deg, lat_deg, decl_deg))
    denom = math.cos(lat) * math.cos(dec)
    if abs(denom) < 1e-12: return None
    c = (math.sin(alt) - math.sin(lat) * math.sin(dec)) / denom
    if c > 1 or c < -1: return None
    return math.degrees(math.acos(c))

def asr_altitude(lat_deg, decl_deg, ratio=1.0):
    noon_alt = 90.0 - abs(lat_deg - decl_deg)
    if noon_alt <= 0: return None
    cot_noon = 1.0 / math.tan(math.radians(noon_alt))
    return math.degrees(math.atan(1.0 / (ratio + cot_noon)))

# ============================================================
# Formatting
# ============================================================

def fmt_ampm(h):
    if h is None: return "--:-- --"
    h %= 24
    hh = int(h); mm = int(round((h - hh) * 60))
    if mm == 60: hh = (hh + 1) % 24; mm = 0
    return f"{hh % 12 or 12}:{mm:02d} {'AM' if hh < 12 else 'PM'}"

def span(a, b):
    if a is None and b is None: return "—"
    if a is None: return f"until {fmt_ampm(b)}"
    if b is None: return f"from {fmt_ampm(a)}"
    if abs(a - b) < 1 / 120: return fmt_ampm(a)
    return f"{fmt_ampm(a)} → {fmt_ampm(b)}"

# ============================================================
# Calculation
# ============================================================

def calculate(y, m, d, lat, lon, tz, fajr_angle, isha_angle, asr_ratio,
              asr_early_fraction, elevation, temperature, pressure):
    decl, EoT = solar_position_spa(
        date_cls(y, m, d), lat, lon, tz,
        elevation=elevation, temperature=temperature, pressure_mbar=pressure,
    )
    noon = 12.0 - lon / 15.0 - EoT / 15.0 + tz

    def before(alt):
        a = hour_angle(alt, lat, decl)
        return noon - a / 15.0 if a is not None else None

    def after(alt):
        a = hour_angle(alt, lat, decl)
        return noon + a / 15.0 if a is not None else None

    T_fajr    = before(-fajr_angle)
    T_sunrise = before(-0.833)
    T_spear   = before(SPEAR_ALT)
    T_duha    = before(DUHA_ALT)
    T_asr     = after(asr_altitude(lat, decl, asr_ratio))
    T_yellow  = after(YELLOW_ALT)
    T_maghrib = after(-0.833)
    T_isha    = after(-isha_angle)

    T_istiwa = noon
    T_zawal  = noon
    T_zenith_start = T_istiwa - ZENITH_BEFORE / 60.0
    T_zenith_end   = T_istiwa + ZENITH_AFTER  / 60.0
    T_dhuhr = T_zawal + DHUHR_OFFSET_MINUTES / 60.0

    if T_sunrise is None or T_spear is None:
        sys.exit("[FATAL] sunrise or spear is None")
    if T_sunrise >= T_spear:
        sys.exit("[FATAL] sunrise >= spear")

    T_asr_early_end = (T_asr + asr_early_fraction * (T_yellow - T_asr)) \
        if (T_asr is not None and T_yellow is not None) else None

    if T_maghrib is not None and T_fajr is not None:
        night_len = (T_fajr + 24.0) - T_maghrib
        T_midnight   = T_maghrib + night_len / 2.0
        T_last_third = T_maghrib + (2.0 / 3.0) * night_len
    else:
        T_midnight = T_last_third = None

    T_duha_best_end   = T_zenith_start - 5.0 / 60.0
    T_isha_best_start = (T_isha + T_midnight) / 2.0 if (T_isha and T_midnight) else None

    return {
        "fajr": T_fajr, "sunrise": T_sunrise, "spear": T_spear,
        "duha_warm": T_duha, "istiwa": T_istiwa, "zawal": T_zawal,
        "dhuhr": T_dhuhr, "asr": T_asr, "yellow": T_yellow,
        "asr_early_end": T_asr_early_end, "maghrib": T_maghrib, "isha": T_isha,
        "midnight": T_midnight, "last_third": T_last_third,
        "zenith_start": T_zenith_start, "zenith_end": T_zenith_end,
        "duha_best_start": T_duha, "duha_best_end": T_duha_best_end,
        "isha_best_start": T_isha_best_start,
    }

# ============================================================
# Report
# ============================================================

def print_report(r, a, tz_label, fajr_src, isha_src):
    line = "=" * 84
    print(f"\n{line}")
    print(f"  HADITH-BASED PRAYER TIMES  —  {VERSION}")
    print(f"{line}")
    print(f"  Date       : {a.date}")
    print(f"  Location   : {a.lat:.4f}°, {a.lon:.4f}°   Elev: {a.elev} m")
    print(f"  Timezone   : {tz_label}  (UTC{a.tz_offset:+.1f})")
    print(f"  Angles     : Fajr={r['fajr_angle']}° ({fajr_src})  "
          f"Isha={r['isha_angle']}° ({isha_src})")
    print(f"  Required   : AsrRatio={a.asr_ratio}")
    print(f"  Conventions: Spear={SPEAR_ALT}°  Duha={DUHA_ALT}°  "
          f"Yellow={YELLOW_ALT}°  ZenithBefore={ZENITH_BEFORE}min  "
          f"AsrEarlyFraction={a.asr_early_fraction}")

    print(f"\n  PRAYER WINDOWS  (chronological, forbidden intervals between)")
    print("  " + "-" * 82)
    print(f"  {'':<12}{'WINDOW':<34}{'BEST TIME':<32}")
    print("  " + "-" * 82)

    def prow(name, win, best):
        w = span(*win) if win else "—"
        b = best if best else ""
        print(f"  {name:<12}{w:<34}{b:<32}")

    prow("Fajr", (r["fajr"], r["sunrise"]), f"best: {fmt_ampm(r['fajr'])}")
    prow("Forbidden", (r["sunrise"], r["spear"]), "(nafl — after Fajr until spear height)")
    prow("Ishraq", (r["spear"], r["zenith_start"]), f"best: {fmt_ampm(r['spear'])}")
    prow("Duha", (r["spear"], r["zenith_start"]), f"best: {span(r['duha_best_start'], r['duha_best_end'])}")
    prow("Forbidden", (r["zenith_start"], r["zenith_end"]), "(nafl — zenith)")
    prow("Dhuhr", (r["dhuhr"], r["asr"]), f"best: {fmt_ampm(r['dhuhr'])}")
    prow("Asr", (r["asr"], r["yellow"]), f"best: {span(r['asr'], r['asr_early_end'])} (pray early)")
    prow("Forbidden", (r["yellow"], r["maghrib"]), "(all prayer — sunset approach)")
    prow("Maghrib", (r["maghrib"], r["isha"]), f"best: {fmt_ampm(r['maghrib'])}")
    prow("Isha", (r["isha"], r["midnight"]), f"best: {span(r['isha_best_start'], r['midnight'])}")
    prow("Tahajjud", (r["isha"], r["fajr"]), f"best: {span(r['last_third'], r['fajr'])}")
    prow("Witr", (r["isha"], r["fajr"]), f"best: {span(r['last_third'], r['fajr'])}")

    print(f"\n  SOLAR NOON ANCHORS")
    print("  " + "-" * 82)
    print(f"  Istiwa' — sun at zenith (peak)              : {fmt_ampm(r['istiwa'])}")
    print(f"  Zawal   — sun begins decline                : {fmt_ampm(r['zawal'])}")
    print(f"  Dhuhr opens (Zawal + {DHUHR_OFFSET_MINUTES} min)         : {fmt_ampm(r['dhuhr'])}")
    print(f"  Zenith precaution begins                    : {fmt_ampm(r['zenith_start'])}")
    print(f"  Zenith precaution ends                      : {fmt_ampm(r['zenith_end'])}")
    print(f"\n{line}\n")

# ============================================================
# CLI
# ============================================================

def parse_tz(tz_str, for_date):
    try:
        off = float(tz_str)
        return off, f"UTC{off:+.1f}"
    except ValueError:
        pass
    if ZoneInfo is not None:
        try:
            zone = ZoneInfo(tz_str)
            probe = datetime(for_date.year, for_date.month, for_date.day,
                             12, 0, 0, tzinfo=zone)
            return probe.utcoffset().total_seconds() / 3600.0, tz_str
        except Exception:
            pass
    sys.exit(f"[FATAL] cannot interpret timezone '{tz_str}'")

def main():
    p = argparse.ArgumentParser(
        description="Hadith-based prayer time calculator (PCD + NREL SPA).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--lat", type=float, required=True)
    p.add_argument("--lon", type=float, required=True)
    p.add_argument("--tz", type=str, required=True)
    p.add_argument("--date", type=str, required=True, help="YYYY-MM-DD")
    p.add_argument("--asr-ratio", type=float, required=True, choices=[1.0, 2.0])

    p.add_argument("--elev", type=float, default=0.0)
    p.add_argument("--asr-early-fraction", type=float, default=0.33)

    p.add_argument("--fajr-angle", type=float, default=None)
    p.add_argument("--isha-angle", type=float, default=None)
    p.add_argument("--temperature", type=float, default=15.0)
    p.add_argument("--pressure", type=float, default=1013.25)
    p.add_argument("--shafaq", type=str, default="general",
                   choices=["general", "ahmer", "abyad"])

    a = p.parse_args()

    if not (0.0 <= a.asr_early_fraction <= 1.0):
        sys.exit("Error: --asr-early-fraction must be between 0 and 1.")

    try:
        d = datetime.strptime(a.date, "%Y-%m-%d").date()
    except ValueError:
        sys.exit("--date must be YYYY-MM-DD")

    a.tz_offset, tz_label = parse_tz(a.tz, d)

    pcd_fajr, pcd_isha = get_pcd_angles(
        d, lat=a.lat, lng=a.lon, elevation=a.elev,
        temperature=a.temperature, pressure=a.pressure, shafaq=a.shafaq,
    )

    if a.fajr_angle is not None:
        fajr_angle, fajr_src = a.fajr_angle, "override"
    else:
        fajr_angle, fajr_src = pcd_fajr, "PCD"

    if a.isha_angle is not None:
        isha_angle, isha_src = a.isha_angle, "override"
    else:
        isha_angle, isha_src = pcd_isha, "PCD"

    r = calculate(
        d.year, d.month, d.day, a.lat, a.lon, a.tz_offset,
        fajr_angle, isha_angle, a.asr_ratio, a.asr_early_fraction,
        a.elev, a.temperature, a.pressure,
    )
    r["fajr_angle"] = fajr_angle
    r["isha_angle"] = isha_angle
    print_report(r, a, tz_label, fajr_src, isha_src)

if __name__ == "__main__":
    main()
```

**Run for Dhaka:**

```bash
python prayer-times-spa-cli.py \
  --lat 23.836468 --lon 90.3695392 --tz Asia/Dhaka --date 2026-09-16 \
  --asr-ratio 1.0
```

---

## Summary of the New Interface

| Argument | regular-cli | pcd-cli | spa-cli |
| :--- | :--- | :--- | :--- |
| `--lat` | required | required | required |
| `--lon` | required | required | required |
| `--tz` | required | required | required |
| `--date` | required | required | required |
| `--fajr-angle` | **required** | optional override | optional override |
| `--isha-angle` | **required** | optional override | optional override |
| `--asr-ratio` | required | required | required |
| `--elev` | optional | optional | optional |
| `--asr-early-fraction` | optional (0.33) | optional (0.33) | optional (0.33) |
| **Required count** | **7** | **5** | **5** |

Hardcoded (no CLI flag): `SPEAR_ALT=5.0`, `DUHA_ALT=15.0`, `YELLOW_ALT=4.0`, `ZENITH_BEFORE=15.0`, `ZENITH_AFTER=0.0`.

## What Changed in the Asr Best-Time Computation

Before (v18):
```python
T_asr_early_end = min(T_asr + asr_early_min/60.0, T_yellow)
```

After (v19):
```python
T_asr_early_end = T_asr + asr_early_fraction * (T_yellow - T_asr)
```

For Dhaka in September: Asr opens at 3:20 PM, yellow at 5:41 PM, window = 141 min.
- v18 default 60 min → best time ends 4:20 PM (43% of window)
- v19 default 0.33 → best time ends ~4:06 PM (33% of window)

In winter, when the window is shorter (say 90 min), v19 scales to ~30 min, whereas v18 kept the 60 min fixed — which would eat 67% of the window. The fraction is scale-invariant; the minutes were not.