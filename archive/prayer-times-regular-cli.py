#!/usr/bin/env python3
"""
Hadith-Based Islamic Prayer Time Calculator (CLI) — v20 REGULAR
---------------------------------------------------------------
7 required args: --lat --lon --tz --date --fajr-angle --isha-angle --asr-ratio
Five convention constants hardcoded. Optional: --elev, --asr-early-fraction.

The three forbidden intervals are labelled with the exact wording of
Sahih Muslim 831 (sunrise, zenith, sunset-approach). The additional
Bukhari 586 prohibition ("no prayer after Fajr till sunrise, no prayer
after Asr till sunset") is explained in a note and is NOT computed
separately, because its start depends on when the worshipper prayed.

Usage:
  python prayer-times-regular-cli.py \
    --lat 23.836468 --lon 90.3695392 --tz Asia/Dhaka --date 2026-09-16 \
    --fajr-angle 18.0 --isha-angle 17.0 --asr-ratio 1.0
"""

VERSION = "v20 REGULAR"
DHUHR_OFFSET_MINUTES = 2.5

# --- Hardcoded convention constants (documented defaults) ---
SPEAR_ALT = 5.0  # "height of a spear"  → Ishraq window opens
DUHA_ALT = 15.0  # "heat of sand"        → Duha best time begins
YELLOW_ALT = 4.0  # "sun draws near to setting" → sunset-approach forbidden
ZENITH_BEFORE = 15.0  # minutes before Istiwa' for zenith precaution
ZENITH_AFTER = 0.0  # minutes after Istiwa' before Dhuhr opens

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
    if EoT > 180:
        EoT -= 360
    if EoT < -180:
        EoT += 360
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

def calculate(y, m, d, lat, lon, tz, fajr_angle, isha_angle, asr_ratio, asr_early_fraction):
    jd = julian_day(y, m, d)
    decl, EoT = solar_position(jd)
    noon = 12.0 - lon / 15.0 - EoT / 15.0 + tz

    def before(alt):
        a = hour_angle(alt, lat, decl)
        return noon - a / 15.0 if a is not None else None

    def after(alt):
        a = hour_angle(alt, lat, decl)
        return noon + a / 15.0 if a is not None else None

    T_fajr = before(-fajr_angle)
    T_sunrise = before(-0.833)
    T_spear = before(SPEAR_ALT)
    T_duha = before(DUHA_ALT)
    T_asr = after(asr_altitude(lat, decl, asr_ratio))
    T_yellow = after(YELLOW_ALT)
    T_maghrib = after(-0.833)
    T_isha = after(-isha_angle)

    T_istiwa = noon
    T_zawal = noon
    T_zenith_start = T_istiwa - ZENITH_BEFORE / 60.0
    T_zenith_end = T_istiwa + ZENITH_AFTER / 60.0
    T_dhuhr = T_zawal + DHUHR_OFFSET_MINUTES / 60.0

    if T_sunrise is None or T_spear is None:
        sys.exit("[FATAL] sunrise or spear is None (polar geometry?)")
    if T_sunrise >= T_spear:
        sys.exit("[FATAL] sunrise >= spear")

    T_asr_early_end = (T_asr + asr_early_fraction * (T_yellow - T_asr)) \
        if (T_asr is not None and T_yellow is not None) else None

    if T_maghrib is not None and T_fajr is not None:
        night_len = (T_fajr + 24.0) - T_maghrib
        T_midnight = T_maghrib + night_len / 2.0
        T_last_third = T_maghrib + (2.0 / 3.0) * night_len
    else:
        T_midnight = T_last_third = None

    T_duha_best_end = T_zenith_start - 5.0 / 60.0
    T_isha_best_start = (T_isha + T_midnight) / 2.0 if (T_isha and T_midnight) else None

    return {
        "fajr": T_fajr,
        "sunrise": T_sunrise,
        "spear": T_spear,
        "duha_warm": T_duha,
        "istiwa": T_istiwa,
        "zawal": T_zawal,
        "dhuhr": T_dhuhr,
        "asr": T_asr,
        "yellow": T_yellow,
        "asr_early_end": T_asr_early_end,
        "maghrib": T_maghrib,
        "isha": T_isha,
        "midnight": T_midnight,
        "last_third": T_last_third,
        "zenith_start": T_zenith_start,
        "zenith_end": T_zenith_end,
        "duha_best_start": T_duha,
        "duha_best_end": T_duha_best_end,
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
    prow("Forbidden", (r["sunrise"], r["spear"]), "(sun begins to rise → fully up)")
    prow("Ishraq", (r["spear"], r["zenith_start"]), f"best: {fmt_ampm(r['spear'])}")
    prow("Duha", (r["spear"], r["zenith_start"]), f"best: {span(r['duha_best_start'], r['duha_best_end'])}")
    prow("Forbidden", (r["zenith_start"], r["zenith_end"]), "(sun at height → passes meridian)")
    prow("Dhuhr", (r["dhuhr"], r["asr"]), f"best: {fmt_ampm(r['dhuhr'])}")
    prow("Asr", (r["asr"], r["yellow"]), f"best: {span(r['asr'], r['asr_early_end'])} (pray early)")
    prow("Forbidden", (r["yellow"], r["maghrib"]), "(sun draws near to setting → sets)")
    prow("Maghrib", (r["maghrib"], r["isha"]), f"best: {fmt_ampm(r['maghrib'])}")
    prow("Isha", (r["isha"], r["midnight"]), f"best: {span(r['isha_best_start'], r['midnight'])}")
    prow("Tahajjud", (r["isha"], r["fajr"]), f"best: {span(r['last_third'], r['fajr'])}")
    prow("Witr", (r["isha"], r["fajr"]), f"best: {span(r['last_third'], r['fajr'])}")

    print(f"\n  SOLAR NOON ANCHORS")
    print("  " + "-" * 82)
    print(f"  Istiwa' — sun at zenith (peak)              : {fmt_ampm(r['istiwa'])}")
    print(f"  Zawal   — sun begins decline                : {fmt_ampm(r['zawal'])}")
    print(f"  Dhuhr opens (Zawal + {DHUHR_OFFSET_MINUTES} min)         : "
          f"{fmt_ampm(r['dhuhr'])}")
    print(f"  Zenith precaution begins                    : "
          f"{fmt_ampm(r['zenith_start'])}")
    print(f"  Zenith precaution ends                      : "
          f"{fmt_ampm(r['zenith_end'])}")

    print(f"\n  THREE FORBIDDEN TIMES  (Sahih Muslim 831)")
    print("  " + "-" * 82)
    print(f"  \"...when the sun begins to rise till it is fully up,")
    print(f"   when the sun is at its height at midday till it passes")
    print(f"   over the meridian, and when the sun draws near to setting")
    print(f"   till it sets.\"")

    print(f"\n  NOTE ON ADDITIONAL FORBIDDEN TIMES (Sahih al-Bukhari 586)")
    print("  " + "-" * 82)
    print(f"  \"There is no prayer after the morning prayer till the sun")
    print(f"   rises, and there is no prayer after the 'Asr prayer till")
    print(f"   the sun sets.\"")
    print(f"  This additional prohibition is not computed separately:")
    print(f"    • Its start depends on when YOU finish praying Fajr / Asr")
    print(f"    • It overlaps with the sunrise and sunset-approach intervals")
    print(f"    • It is a nafl-only restriction; the obligatory prayers remain valid")
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
            probe = datetime(for_date.year, for_date.month, for_date.day, 12, 0, 0, tzinfo=zone)
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
    p.add_argument("--tz", type=str, required=True, help="Numeric offset (+6) or IANA name (Asia/Dhaka)")
    p.add_argument("--date", type=str, required=True, help="YYYY-MM-DD")
    p.add_argument("--fajr-angle",
                   type=float,
                   required=True,
                   help="Fajr solar DEPRESSION in degrees (positive). Common: 18.0")
    p.add_argument("--isha-angle",
                   type=float,
                   required=True,
                   help="Isha solar DEPRESSION in degrees (positive). Common: 17.0")
    p.add_argument("--asr-ratio",
                   type=float,
                   required=True,
                   choices=[1.0, 2.0],
                   help="Asr shadow ratio: 1.0 (standard) or 2.0 (Hanafi)")

    p.add_argument("--elev", type=float, default=0.0, help="Elevation in metres (optional, default 0)")
    p.add_argument("--asr-early-fraction",
                   type=float,
                   default=0.33,
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
        d.year,
        d.month,
        d.day,
        a.lat,
        a.lon,
        a.tz_offset,
        a.fajr_angle,
        a.isha_angle,
        a.asr_ratio,
        a.asr_early_fraction,
    )
    print_report(r, a, tz_label)

if __name__ == "__main__":
    main()
