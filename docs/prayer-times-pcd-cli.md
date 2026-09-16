You've shown two outputs and asked which is more accurate. Let me identify which is which first, because the differences are subtle and the answer depends on it.

## Identifying the Two Outputs

| Feature | Output 1 | Output 2 |
| :--- | :--- | :--- |
| Fajr starts | 4:29 AM | 4:21 AM |
| Isha starts | 7:13 PM | 7:17 PM |
| Islamic midnight | 11:16 PM | 11:11 PM |
| Last third begins | 1:00 AM | 12:54 AM |
| Implied Fajr angle | ~18.0° | ~18.5° (larger) |
| Implied Isha angle | ~17.0° | ~17.3° (larger) |

**Output 1 is the fixed-angle version (v12 with defaults).**
**Output 2 is the PCD dynamic version (v13).**

## Why the PCD Values Differ From Fixed Angles

The PCD algorithm returned angles for Dhaka on 2026-09-16 that are **larger in magnitude** than the fixed 18°/17° you were using:

- Fajr: PCD ≈ 18.5° vs fixed 18.0° → sun must go deeper below horizon → Fajr starts **earlier** (4:21 vs 4:29)
- Isha: PCD ≈ 17.3° vs fixed 17.0° → sun must go deeper below horizon → Isha starts **later** (7:17 vs 7:13)

Both changes increase the night length slightly, which is why Tahajjud's last third moved 6 minutes earlier.

## Which Is More Accurate?

**PCD is more accurate in theory and in empirical validation.** Here is why:

| Criterion | Fixed 18°/17° | PCD |
| :--- | :--- | :--- |
| Adapts to season | ❌ No | ✅ Yes (MSC seasonal model) |
| Adapts to latitude | ❌ No | ✅ Yes |
| Adapts to elevation | ❌ No | ✅ Yes |
| Includes refraction | ❌ No | ✅ Bennett/Saemundsson |
| Includes Earth-Sun distance | ❌ No | ✅ ±0.015° |
| Empirical MAE vs. observed twilight | ~3–5 min | **~0.6–1.3 min** |

The `pray-calc` wiki documents an 18-city study showing PCD tracks observation-calibrated references within **1 minute** across latitudes 6°S–51°N, while all 14 fixed-angle methods average **13.5× more error** even at their home cities.

## But There Is a Caveat for Dhaka Specifically

PCD is more accurate **globally**. For Dhaka specifically, you need to check one thing: **does the PCD angle match what you actually see in the sky?**

The Islamic Foundation Bangladesh (IFB) uses a fixed 18° for both Fajr and Isha. If IFB's 18° was calibrated by observation in Dhaka, then PCD's 18.5° for Fajr might be **too deep** — it would push Fajr 8 minutes earlier than IFB, which could be before the true dawn actually appears.

Three possibilities:

1. **PCD is right and IFB is slightly off.** IFB's 18° may be a generic value borrowed from the MWL, not locally calibrated.
2. **IFB is right and PCD's MSC model over-corrects for Dhaka's latitude.** Possible if the MSC model is biased toward Middle Eastern observations.
3. **Both are within the tolerance of the hadith.** The hadith describe "true dawn," not a specific angle. A 4-minute difference (4:21 vs 4:25) is within observational uncertainty.

## How to Know Which Is Right for Dhaka

You cannot determine this by calculation alone. You must **observe**:

1. **Pick a clear morning.** Go outside 30 minutes before the calculated Fajr.
2. **Watch the eastern horizon.** The true dawn (*al-Fajr al-Ṣādiq*) is the moment a **horizontal white light** spreads across the horizon — distinct from the earlier, vertical, cone-shaped false dawn (*al-Fajr al-Kādhib*).
3. **Note the clock time** when you see that horizontal white light.
4. **Compare:**
   - If observed dawn = 4:21 AM → PCD is right
   - If observed dawn = 4:29 AM → fixed 18° is right
   - If observed dawn = 4:25 AM → both are close; split the difference

Repeat for 3–5 clear mornings across different seasons. If PCD consistently matches your observation, trust it. If IFB's fixed angle consistently matches, trust that. If neither does, calibrate a local angle from your observations and pass it via `--fajr-angle`.

## Practical Recommendation

| Goal | Use |
| :--- | :--- |
| Maximum theoretical accuracy | **PCD** (v13, default) |
| Matching IFB / local mosque timetable | Fixed 18° / 17° (v12 or override PCD) |
| Maximum accuracy after local calibration | PCD + 3–5 observed mornings to verify |
| Conservative (safest for prayer) | Use the earlier of the two (PCD) for Fajr, the later of the two (PCD) for Isha — this ensures you don't pray before true dawn or before redness disappears |

For Dhaka, I would **start with PCD** (it is the more principled method), then verify with 3–5 observed mornings. If PCD matches the sky, keep it. If IFB's 18° matches better, override:

```bash
python prayer-times-cli.py --lat 23.836468 --lon 90.3695392 --tz Asia/Dhaka --elev 9 \
  --fajr-angle 18.0 --isha-angle 17.0
```

But do not assume the fixed value is correct just because it is familiar. The hadith command you to pray at **true dawn**, not at **18°**. The angle is a tool; the observation is the truth.