#!/usr/bin/env python3
"""
Hadith-Based Islamic Prayer Time Calculator (CLI) — v20 PCD
-----------------------------------------------------------
5 required args: --lat --lon --tz --date --asr-ratio
PCD computes Fajr/Isha angles. Optional overrides via --fajr-angle/--isha-angle.
Five convention constants hardcoded. Optional: --elev, --asr-early-fraction.

The three forbidden intervals are labelled with the exact wording of
Sahih Muslim 831 (sunrise, zenith, sunset-approach). The additional
Bukhari 586 prohibition ("no prayer after Fajr till sunrise, no prayer
after Asr till sunset") is explained in a note and is NOT computed
separately, because its start depends on when the worshipper prayed.

Usage:
  python prayer-times-pcd-cli.py \
    --lat 23.836468 --lon 90.3695392 --tz Asia/Dhaka --date 2026-09-16 \
    --asr-ratio 1.0
"""

VERSION = "v20 PCD"
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
from datetime import datetime, date as date_cls, timezone

try:
    from zoneinfo import ZoneInfo
except ImportError:
    ZoneInfo = None

# ============================================================
# PCD ALGORITHM (Moonsighting Committee Worldwide seasonal model)
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
    eps0 = (23.0 + 26.0 / 60.0 + 21.448 / 3600.0 - (46.8150 * T + 0.00059 * T * T - 0.001813 * T * T * T) / 3600.0)
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
    if dyy < 91:
        return a + ((b - a) / 91) * dyy
    if dyy < 137:
        return b + ((c - b) / 46) * (dyy - 91)
    if dyy < 183:
        return c + ((d - c) / 46) * (dyy - 137)
    if dyy < 229:
        return d + ((c - d) / 46) * (dyy - 183)
    if dyy < 275:
        return c + ((b - c) / 46) * (dyy - 229)
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
    cos_phi = math.cos(phi)
    sin_phi = math.sin(phi)
    cos_delta = math.cos(delta)
    sin_delta = math.sin(delta)
    h0 = -0.833 * DEG
    sin_h0 = math.sin(h0)
    denom = cos_phi * cos_delta
    if abs(denom) < 1e-10:
        return float("nan")
    cos_h_rise = (sin_h0 - sin_phi * sin_delta) / denom
    if cos_h_rise < -1 or cos_h_rise > 1:
        return float("nan")
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
    theta = ecl_lon
    phi = lat_abs_deg * DEG
    return (0.03 * math.sin(theta) - 0.05 * math.cos(theta) + 0.02 * math.sin(2 * theta) + 0.02 * math.cos(2 * theta) -
            0.008 * phi * math.sin(theta) + 0.004 * phi * math.cos(theta))

def _clip(v, lo, hi):
    return max(lo, min(hi, v))

def _round3(v):
    return round(v, 3)

def get_pcd_angles(d, lat, lng=0.0, elevation=0.0, temperature=15.0, pressure=1013.25, shafaq="general"):
    """Return (fajr_angle, isha_angle) as POSITIVE depression angles (degrees)."""
    jd = _to_julian_date(d)
    decl, r, ecl_lon = _solar_ephemeris(jd)
    msc_fajr_min = _get_msc_fajr(d, lat)
    msc_isha_min = _get_msc_isha(d, lat, shafaq)
    fajr_base = _minutes_to_depression(msc_fajr_min, lat, decl)
    isha_base = _minutes_to_depression(msc_isha_min, lat, decl)
    if not math.isfinite(fajr_base):
        fajr_base = 18.0
    if not math.isfinite(isha_base):
        isha_base = 18.0
    r_corr = _earth_sun_distance_correction(r)
    fourier_corr = _fourier_smoothing_correction(ecl_lon, abs(lat))
    refr_fajr = _atmospheric_refraction(-(fajr_base + 0.5), pressure, temperature)
    refr_isha = _atmospheric_refraction(-(isha_base + 0.5), pressure, temperature)
    horizon_dip = 1.06 * math.sqrt(max(elevation, 0.0) / 1000.0)
    elev_corr = horizon_dip * 0.3
    raw_fajr = fajr_base + r_corr + fourier_corr + refr_fajr + elev_corr
    raw_isha = isha_base + r_corr + fourier_corr + refr_isha + elev_corr
    return (_round3(_clip(raw_fajr, ANGLE_MIN, ANGLE_MAX)), _round3(_clip(raw_isha, ANGLE_MIN, ANGLE_MAX)))

# ============================================================
# ASTRONOMY (Meeus) for the rest of the prayer times
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
        description="Hadith-based prayer time calculator (PCD dynamic angles). "
        "Fajr/Isha angles computed by PCD unless overridden.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--lat", type=float, required=True)
    p.add_argument("--lon", type=float, required=True)
    p.add_argument("--tz", type=str, required=True, help="Numeric offset (+6) or IANA name (Asia/Dhaka)")
    p.add_argument("--date", type=str, required=True, help="YYYY-MM-DD")
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

    # Optional PCD overrides
    p.add_argument("--fajr-angle",
                   type=float,
                   default=None,
                   help="Override PCD Fajr depression angle (positive degrees).")
    p.add_argument("--isha-angle",
                   type=float,
                   default=None,
                   help="Override PCD Isha depression angle (positive degrees).")
    p.add_argument("--temperature",
                   type=float,
                   default=15.0,
                   help="Ambient temperature (°C) for the refraction model.")
    p.add_argument("--pressure",
                   type=float,
                   default=1013.25,
                   help="Atmospheric pressure (mbar) for the refraction model.")
    p.add_argument("--shafaq",
                   type=str,
                   default="general",
                   choices=["general", "ahmer", "abyad"],
                   help="Isha twilight mode: general (blended), ahmer (red), "
                   "abyad (white).")

    a = p.parse_args()

    if not (0.0 <= a.asr_early_fraction <= 1.0):
        sys.exit("Error: --asr-early-fraction must be between 0 and 1.")
    if a.fajr_angle is not None and (a.fajr_angle <= 0 or a.fajr_angle >= 90):
        sys.exit("Error: --fajr-angle override must be POSITIVE (0 < x < 90).")
    if a.isha_angle is not None and (a.isha_angle <= 0 or a.isha_angle >= 90):
        sys.exit("Error: --isha-angle override must be POSITIVE (0 < x < 90).")

    try:
        d = datetime.strptime(a.date, "%Y-%m-%d").date()
    except ValueError:
        sys.exit("--date must be YYYY-MM-DD")

    a.tz_offset, tz_label = parse_tz(a.tz, d)

    pcd_fajr, pcd_isha = get_pcd_angles(
        d,
        lat=a.lat,
        lng=a.lon,
        elevation=a.elev,
        temperature=a.temperature,
        pressure=a.pressure,
        shafaq=a.shafaq,
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
        d.year,
        d.month,
        d.day,
        a.lat,
        a.lon,
        a.tz_offset,
        fajr_angle,
        isha_angle,
        a.asr_ratio,
        a.asr_early_fraction,
    )
    r["fajr_angle"] = fajr_angle
    r["isha_angle"] = isha_angle
    print_report(r, a, tz_label, fajr_src, isha_src)

if __name__ == "__main__":
    main()
