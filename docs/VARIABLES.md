# README — Hadith-Based Prayer Time Calculator

This document explains every input and internal constant used by the three CLIs (`prayer-times-regular-cli.py`, `prayer-times-pcd-cli.py`, `prayer-times-spa-cli.py`). Each value is classified as:

- **Required** — must be supplied on the command line
- **Convention** — hardcoded constant, documented below
- **Optional** — CLI flag with a default
- **Derived** — computed internally, not user-supplied

---

## 1. Location and Time (Required)

### `--lat` (latitude, degrees)
Your position north or south of the equator. Used by the hour-angle solver. No hadith basis — it is a geographic coordinate.

### `--lon` (longitude, degrees)
Your position east or west of Greenwich. Determines solar noon relative to your clock. No hadith basis.

### `--tz` (timezone)
Numeric offset (`+6`) or IANA name (`Asia/Dhaka`). Resolved to the UTC offset **for the target date**, so DST is handled correctly. No hadith basis.

### `--date` (`YYYY-MM-DD`)
The observer's local calendar day. Determines solar declination and equation of time. No hadith basis.

### `--elev` (elevation, metres, optional, default 0)
Your elevation above sea level. Used only in the PCD and SPA CLIs to correct the horizon dip for twilight angles. **No hadith basis** — a physical measurement.

---

## 2. Twilight Depression Angles (Required in regular-cli; PCD-computed in pcd-cli and spa-cli)

### `--fajr-angle` (degrees below horizon, positive)
The sun's depression angle at the start of Fajr. **No universal value** — it is a calibration proxy for the hadith phenomenon "true dawn" (*al-Fajr al-Ṣādiq*), the moment a horizontal white light spreads across the eastern horizon, distinct from the earlier vertical false dawn (*al-Fajr al-Kādhib*).

The hadith describe the **phenomenon**, not a degree. Common conventions: 18° (Muslim World League, Karachi), 19.5° (Egypt), 15° (ISNA), 20° (MUIS). Calibrate locally by observing the true dawn.

### `--isha-angle` (degrees below horizon, positive)
The sun's depression angle at the start of Isha. **No universal value** — a proxy for the hadith phenomenon "disappearance of the redness" (*shafaq*). The Prophet (ﷺ) said: *"The time of the 'Isha prayer is until half of the night has passed"* (Sahih Muslim 612a). The **start** is marked by the disappearance of the red twilight. Common conventions: 17° (MWL), 18° (Karachi), 15° (ISNA).

---

## 3. Asr Shadow Ratio (Required)

### `--asr-ratio` (1.0 or 2.0)
The shadow length of an object (in multiples of its height) that marks the start of Asr. This is the **only numerical value directly stated in the hadith**.

- **1.0** (standard — Shafi'i, Maliki, Hanbali): Asr begins when a man's shadow equals his height. The Prophet (ﷺ) said: *"The time of the noon prayer is when the sun passes the meridian and a man's shadow is the same (length) as his height"* (Sahih Muslim 612d).
- **2.0** (Hanafi): Asr begins when the shadow is twice the object's height. Reported as a variant of the same hadith.

---

## 4. Hardcoded Convention Constants

These five values are **not from hadith** and **not calculable**. They are conventions chosen to translate visual descriptions in the hadith into numerical altitudes. They are documented here so the reader understands what assumption each represents.

### `SPEAR_ALT = 5.0`
> "height of a spear" → Ishraq window opens

**What it is:** The sun's altitude above the horizon that corresponds to the hadith description of the sun rising "to the height of a spear." This is the moment the forbidden post-Fajr period ends and the Ishraq (and Duha) window opens.

**Hadith:** The Prophet (ﷺ) said: *"When the sun rises to the height of a spear, then pray"* — the same description applies to the end of the post-Fajr forbidden time and the start of Ishraq. Sahih Muslim 831: *"when the sun begins to rise till it is fully up"* — the forbidden time ends when the sun has "fully up" to spear height.

**Value justification:** 5.0° corresponds to roughly 12–15 minutes after sunrise at mid-latitudes. The height of a spear held at arm's length subtends a small positive angle; 5° is a common convention.

---

### `DUHA_ALT = 15.0`
> "heat of sand" → Duha best time begins

**What it is:** The sun's altitude above the horizon that corresponds to the hadith description of the "heat of the sand." This is the moment the Duha prayer's best-time window opens.

**Hadith:** The Prophet (ﷺ) said: *"The prayer of those who are penitent is offered when the young weaned camels feel the heat of the sand"* (Sahih Muslim 1237).

**Value justification:** 15.0° corresponds to mid-morning at mid-latitudes. The exact angle is not in the hadith; 15° is a conventional proxy for "when the ground becomes noticeably hot."

---

### `YELLOW_ALT = 4.0`
> "sun turns yellow" → sunset-approach forbidden

**What it is:** The sun's altitude above the horizon when its light visibly yellows or oranges. This marks the start of the sunset-approach forbidden interval.

**Hadith:** The Prophet (ﷺ) said: *"The time of 'Asr Prayer comes to an end when the sun becomes yellowish"* (Sahih Muslim). And Uqbah ibn Amir reported: *"There were three times at which Allah's Messenger forbade us to pray... when the sun draws near to setting till it sets"* (Sahih Muslim 831).

**Value justification:** 4.0° is a conventional altitude at which the sun's light appears yellow rather than white. The hadith describes the visual event; 4° is a numerical proxy.

**Important:** This value serves **two purposes**: (1) it ends the Asr preferred window (the "best time" for Asr is before this moment), and (2) it starts the sunset-approach forbidden interval (which ends at sunset).

---

### `ZENITH_BEFORE = 15.0`
> minutes before Istiwa' for zenith precaution

**What it is:** The number of minutes before solar transit (Istiwa') that the zenith forbidden interval begins. This is a **precautionary buffer**, not a measured quantity.

**Hadith:** The Prophet (ﷺ) said: *"There were three times at which Allah's Messenger forbade us to pray... when the sun is at its height at midday till it passes over the meridian"* (Sahih Muslim 831).

**Value justification:** The hadith describes the forbidden time as "when the sun is at its height... till it passes over the meridian." The exact moment of Istiwa is a fleeting instant that cannot be pinpointed by observation. Scholars have adopted different precautionary margins — Ibn Baz used 15–20 minutes before, others use 5 minutes symmetric. The 15-minute convention here is **Ibn Baz's conservative margin**. The user can reduce it if they follow a less conservative scholar.

**Note on Istiwa vs. Zawal:** Istiwa (الاستواء) is when the sun is at its absolute peak — **the last forbidden moment**. Zawal (الزوال) is when the sun begins to decline — **the first permissible moment**, when Dhuhr opens. Both occur at the same astronomical instant (solar transit). The buffer before Istiwa ensures no prayer falls inside the unmeasurable forbidden instant.

---

### `ZENITH_AFTER = 0.0`
> minutes after Istiwa' before Dhuhr opens

**What it is:** The number of minutes after Istiwa' that Dhuhr is delayed. Set to 0 because the hadith says the forbidden time ends **"when the sun passes over the meridian"** — that is exactly when Dhuhr opens. There is no post-noon buffer in the hadith.

**Value justification:** Adding a buffer after Istiwa' would contradict the hadith's wording "till it passes over the meridian" — the prohibition ends the instant the sun declines.

---

## 5. Asr Best-Time Fraction (Optional)

### `--asr-early-fraction` (default 0.33)
The fraction of the Asr preferred window (from Asr opening to sun-yellowing) that is considered the "best time."

**Hadith:** The Prophet (ﷺ) encouraged praying Asr early. Sahih Muslim has a chapter titled *"It is recommended to pray 'Asr early"* (باب استحباب التبكير بالعصر). Bukhari 546: Aisha (RA) said the Prophet "used to pray the 'Asr prayers at a time when the sunshine was still inside my chamber and no shadow had yet appeared in it."

**Value justification:** No hadith specifies a duration. A **fraction** is scale-invariant — for Dhaka in September (141-min window), 0.33 → ~46 min; in winter (90-min window), 0.33 → ~30 min. This is more faithful to "pray early" than a fixed minute count, because it adapts to the day length.

**Set to 0.0** for only the opening moment; **set to 1.0** for the entire window until yellowing.

---

## 6. Internal Constants (Not CLI Arguments)

### `DHUHR_OFFSET_MINUTES = 2.5`
Minutes added to solar transit (Zawal) before Dhuhr opens. This matches the convention used by `pray-calc` and other authorities — it ensures the sun has visibly declined from the zenith before Dhuhr begins. No hadith specifies 2.5 minutes; it is a **small buffer** for the "sun has passed the meridian" criterion.

### `SUNRISE_ALT / SUNSET_ALT = −0.833°`
The standard astronomical altitude of the sun's upper limb at sunrise/sunset, including atmospheric refraction. **No hadith basis** — an astronomical constant.

### `LAT_SCALE = 55.0`, `ANGLE_MIN = 10.0`, `ANGLE_MAX = 22.0`
PCD algorithm constants (Moonsighting Committee Worldwide model). Not user-tunable.

---

## 7. Optional Physics (pcd-cli and spa-cli only)

### `--temperature` (default 15°C)
Ambient temperature for the atmospheric refraction model. Affects the refraction correction at twilight angles. No hadith basis.

### `--pressure` (default 1013.25 mbar)
Atmospheric pressure for the refraction model. No hadith basis.

### `--shafaq` (default `general`)
Isha twilight mode for the PCD algorithm:
- `general` — blended, reduces hardship at high latitudes
- `ahmer` — based on the disappearance of **redness** (*shafaq ahmar*)
- `abyad` — based on the disappearance of **whiteness** (*shafaq abyad*), later

The hadith describe the disappearance of **redness**, which corresponds to `ahmer`. The `general` default is a compromise for high-latitude users where redness never fully disappears in summer.

---

## 8. Summary Table

| Argument / Constant | Type | Default | Hadith Reference |
| :--- | :--- | :--- | :--- |
| `--lat` | Required | — | None (geographic) |
| `--lon` | Required | — | None (geographic) |
| `--tz` | Required | — | None (timezone) |
| `--date` | Required | — | None (calendar) |
| `--elev` | Optional | 0 | None (physical) |
| `--fajr-angle` | Required (regular) | — | "True dawn" — Sahih Muslim 612a |
| `--isha-angle` | Required (regular) | — | "Redness disappears" — Sahih Muslim 612a |
| `--asr-ratio` | Required | — | **Sahih Muslim 612d** (direct) |
| `SPEAR_ALT` | Convention | 5.0 | "Height of a spear" — Sahih Muslim 831 |
| `DUHA_ALT` | Convention | 15.0 | "Heat of sand" — Sahih Muslim 1237 |
| `YELLOW_ALT` | Convention | 4.0 | "Sun turns yellow" — Sahih Muslim |
| `ZENITH_BEFORE` | Convention | 15.0 | "Sun at its height" — Sahih Muslim 831 |
| `ZENITH_AFTER` | Convention | 0.0 | "Till it passes the meridian" — Sahih Muslim 831 |
| `--asr-early-fraction` | Optional | 0.33 | "Pray Asr early" — Sahih Muslim (chapter) |
| `DHUHR_OFFSET_MINUTES` | Internal | 2.5 | "Sun passes meridian" — Sahih Muslim 612d |
| `--temperature` | Optional | 15°C | None (physical) |
| `--pressure` | Optional | 1013.25 mbar | None (physical) |
| `--shafaq` | Optional | general | "Redness disappears" — Sahih Muslim 612a |

---

## 9. Forbidden Intervals

The program computes four forbidden intervals based on hadith:

| Interval | Trigger | Scope | Reference |
| :--- | :--- | :--- | :--- |
| After Fajr → spear height | Sunrise | Nafl only | Sahih Muslim 831; Sahih al-Bukhari 586 |
| Zenith → Zawal | Precaution before Istiwa' | Nafl only | Sahih Muslim 831 |
| After Asr → sunset | Completion of Asr prayer | Nafl only | Sahih al-Bukhari 586 |
| Sunset-approach → sunset | Sun yellowing | All prayer | Sahih Muslim 831 |

**Sahih al-Bukhari 586:** *"Allah's Messenger forbade the offering of two prayers: 1. after the morning prayer till the sun rises. 2. after the 'Asr prayer till the sun sets."*

**Sahih Muslim 831:** *"There were three times at which Allah's Messenger forbade us to pray, or bury our dead: When the sun begins to rise till it is fully up, when the sun is at its height at midday till it passes over the meridian, and when the sun draws near to setting till it sets."*
