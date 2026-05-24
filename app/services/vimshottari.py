"""
Vimshottari mahadasha and antardasha from Moon longitude and birth Julian Date.

Dasha "years" are converted with 365.2422 solar days per year (civil alignment).
JD → calendar uses Swiss Ephemeris `revjul`, matching `julday` in kundali_chart.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import swisseph as swe

from app.config import NAKSHATRAS, VIMSHOTTARI_CHRONOLOGY, VIMSHOTTARI_YEARS
from app.models import BirthChart, DashaPeriod, MahadashaWithAntardashas, VimshottariChart

DAYS_PER_DASHA_YEAR = 365.2422

_chrono_index = {lord: i for i, lord in enumerate(VIMSHOTTARI_CHRONOLOGY)}
assert len(_chrono_index) == len(VIMSHOTTARI_CHRONOLOGY)
assert abs(sum(VIMSHOTTARI_YEARS.values()) - 120.0) < 1e-9
for lord in VIMSHOTTARI_CHRONOLOGY:
    assert lord in VIMSHOTTARI_YEARS


def jd_to_utc_datetime(jd: float) -> datetime:
    """UT Julian date → naive UTC datetime (inverse of `swe.julday`, same convention)."""
    year, month, day, hour_ut = swe.revjul(jd, swe.GREG_CAL)
    midnight = datetime(year, month, day, 0, 0, 0)
    return midnight + timedelta(hours=hour_ut)


def utc_to_birth_timezone(dt_utc: datetime, tz_hours: float) -> datetime:
    """Attach fixed offset matching BirthChart.timezone (hours east of UTC)."""
    tz = timezone(timedelta(hours=tz_hours))
    return dt_utc.replace(tzinfo=timezone.utc).astimezone(tz)


def years_to_days(years: float) -> float:
    return years * DAYS_PER_DASHA_YEAR


def nakshatra_id_from_moon_longitude(moon_longitude: float) -> int:
    """Match `calculate_nakshatra` index (`13.33333`); arc length for balance uses exact 360/27."""
    moon_norm = moon_longitude % 360.0
    idx = int(moon_norm / 13.33333) % 27
    return idx + 1


def next_lord(lord: str) -> str:
    i = _chrono_index[lord]
    return VIMSHOTTARI_CHRONOLOGY[(i + 1) % 9]


def antardasha_order_for_mahadasha(mahadasha_lord: str) -> tuple[str, ...]:
    i = _chrono_index[mahadasha_lord]
    return VIMSHOTTARI_CHRONOLOGY[i:] + VIMSHOTTARI_CHRONOLOGY[:i]


def antardashas_for_mahadasha(
    mahadasha_lord: str,
    mahadasha_years: float,
    start_jd: float,
    tz_hours: float,
) -> list[DashaPeriod]:
    order = antardasha_order_for_mahadasha(mahadasha_lord)
    periods: list[DashaPeriod] = []
    jd = start_jd
    for sub in order:
        dur_y = mahadasha_years * VIMSHOTTARI_YEARS[sub] / 120.0
        dur_d = years_to_days(dur_y)
        end_jd = jd + dur_d
        start_local = utc_to_birth_timezone(jd_to_utc_datetime(jd), tz_hours)
        end_local = utc_to_birth_timezone(jd_to_utc_datetime(end_jd), tz_hours)
        periods.append(
            DashaPeriod(
                lord=sub,
                start=start_local,
                end=end_local,
                duration_years=dur_y,
                duration_days=dur_d,
            )
        )
        jd = end_jd
    return periods


def mahadasha_segments_from_birth(
    opening_lord: str,
    balance_years: float,
) -> list[tuple[str, float]]:
    """Sequence of (lord, duration_years) covering the first 120-year Vimshottari cycle from birth."""
    segments: list[tuple[str, float]] = []
    total = 0.0
    lord = opening_lord
    first = True
    while total < 120.0 - 1e-9:
        if first:
            years = balance_years
            first = False
        else:
            years = VIMSHOTTARI_YEARS[lord]
        remaining = 120.0 - total
        if years > remaining:
            years = remaining
        segments.append((lord, years))
        total += years
        if total >= 120.0 - 1e-9:
            break
        lord = next_lord(lord)
    return segments


def compute_vimshottari(birth_chart: BirthChart, birth_jd: float, moon_longitude: float) -> VimshottariChart:
    k = nakshatra_id_from_moon_longitude(moon_longitude)
    opening_lord = NAKSHATRAS[k]["lord"]
    span = 360.0 / 27.0
    moon_norm = moon_longitude % 360.0
    idx = k - 1
    elapsed = moon_norm - idx * span
    if elapsed < 0:
        elapsed += span
    balance = (span - elapsed) / span * VIMSHOTTARI_YEARS[opening_lord]

    segments = mahadasha_segments_from_birth(opening_lord, balance)
    tz = birth_chart.timezone

    mahadashas: list[MahadashaWithAntardashas] = []
    jd_cursor = birth_jd

    for md_lord, md_years in segments:
        md_days = years_to_days(md_years)
        md_end_jd = jd_cursor + md_days
        md_start_local = utc_to_birth_timezone(jd_to_utc_datetime(jd_cursor), tz)
        md_end_local = utc_to_birth_timezone(jd_to_utc_datetime(md_end_jd), tz)
        md_period = DashaPeriod(
            lord=md_lord,
            start=md_start_local,
            end=md_end_local,
            duration_years=md_years,
            duration_days=md_days,
        )
        antardashas = antardashas_for_mahadasha(md_lord, md_years, jd_cursor, tz)
        mahadashas.append(
            MahadashaWithAntardashas(mahadasha=md_period, antardashas=antardashas)
        )
        jd_cursor = md_end_jd

    return VimshottariChart(mahadashas=mahadashas)


def find_dashas_in_range(
    chart: VimshottariChart,
    start: datetime,
    end: datetime,
) -> list[dict]:
    """
    Return all antardasha periods (with their parent mahadasha context) that
    overlap the half-open interval [start, end].

    Timezone info is stripped before comparison — dasha boundaries span months
    or years, so sub-hour differences from timezone offsets are irrelevant.
    """
    start_naive = start.replace(tzinfo=None)
    end_naive = end.replace(tzinfo=None)

    results = []
    for maha in chart.mahadashas:
        md = maha.mahadasha
        md_start = md.start.replace(tzinfo=None)
        md_end = md.end.replace(tzinfo=None)

        # Skip mahadashas that don't touch the range at all
        if md_end <= start_naive or md_start > end_naive:
            continue

        for antar in maha.antardashas:
            ad_start = antar.start.replace(tzinfo=None)
            ad_end = antar.end.replace(tzinfo=None)

            if ad_end > start_naive and ad_start <= end_naive:
                results.append({
                    "mahadasha": {
                        "lord": md.lord,
                        "start": md.start.strftime("%Y-%m-%d"),
                        "end": md.end.strftime("%Y-%m-%d"),
                        "duration_years": round(md.duration_years, 2),
                    },
                    "antardasha": {
                        "lord": antar.lord,
                        "start": antar.start.strftime("%Y-%m-%d"),
                        "end": antar.end.strftime("%Y-%m-%d"),
                        "duration_years": round(antar.duration_years, 2),
                    },
                })

    return results
