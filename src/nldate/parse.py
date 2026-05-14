from __future__ import annotations

import re
from calendar import monthrange
from datetime import date, timedelta

_WEEKDAY_MAP: dict[str, int] = {
    "monday": 0,
    "mon": 0,
    "tuesday": 1,
    "tue": 1,
    "tues": 1,
    "wednesday": 2,
    "wed": 2,
    "thursday": 3,
    "thu": 3,
    "thur": 3,
    "thurs": 3,
    "friday": 4,
    "fri": 4,
    "saturday": 5,
    "sat": 5,
    "sunday": 6,
    "sun": 6,
}

_MONTH_MAP: dict[str, int] = {
    "january": 1,
    "jan": 1,
    "february": 2,
    "feb": 2,
    "march": 3,
    "mar": 3,
    "april": 4,
    "apr": 4,
    "may": 5,
    "june": 6,
    "jun": 6,
    "july": 7,
    "jul": 7,
    "august": 8,
    "aug": 8,
    "september": 9,
    "sep": 9,
    "sept": 9,
    "october": 10,
    "oct": 10,
    "november": 11,
    "nov": 11,
    "december": 12,
    "dec": 12,
}

_WORD_TO_INT: dict[str, int] = {
    "zero": 0,
    "a": 1,
    "an": 1,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
    "twenty": 20,
    "thirty": 30,
    "forty": 40,
    "fifty": 50,
}

_ORDINAL_TO_INT: dict[str, int] = {
    "first": 1,
    "second": 2,
    "third": 3,
    "fourth": 4,
    "fifth": 5,
    "sixth": 6,
    "seventh": 7,
    "eighth": 8,
    "ninth": 9,
    "tenth": 10,
    "eleventh": 11,
    "twelfth": 12,
    "thirteenth": 13,
    "fourteenth": 14,
    "fifteenth": 15,
    "sixteenth": 16,
    "seventeenth": 17,
    "eighteenth": 18,
    "nineteenth": 19,
    "twentieth": 20,
    "twenty-first": 21,
    "twenty-second": 22,
    "twenty-third": 23,
    "twenty-fourth": 24,
    "twenty-fifth": 25,
    "twenty-sixth": 26,
    "twenty-seventh": 27,
    "twenty-eighth": 28,
    "twenty-ninth": 29,
    "thirtieth": 30,
    "thirty-first": 31,
}

_NUM_WORDS = sorted(_WORD_TO_INT, key=len, reverse=True)
_NUM_PAT = r"(?:\d+|" + "|".join(re.escape(w) for w in _NUM_WORDS) + r")"
_UNIT_PAT = r"(?:years?|months?|weeks?|days?)"
_TERM_RE = re.compile(rf"({_NUM_PAT})\s+({_UNIT_PAT})")


def _to_int(s: str) -> int:
    s = s.strip()
    if s.isdigit():
        return int(s)
    return _WORD_TO_INT[s]


def _add_months(d: date, n: int) -> date:
    month = d.month - 1 + n
    year = d.year + month // 12
    month = month % 12 + 1
    day = min(d.day, monthrange(year, month)[1])
    return d.replace(year=year, month=month, day=day)


def _add_years(d: date, n: int) -> date:
    year = d.year + n
    day = min(d.day, monthrange(year, d.month)[1])
    return d.replace(year=year, day=day)


def _apply_offset(base: date, n: int, unit: str, forward: bool) -> date:
    sign = 1 if forward else -1
    u = unit[:-1] if unit.endswith("s") else unit
    if u == "day":
        return base + timedelta(days=sign * n)
    if u == "week":
        return base + timedelta(weeks=sign * n)
    if u == "month":
        return _add_months(base, sign * n)
    return _add_years(base, sign * n)


def _next_weekday(ref: date, wd: int) -> date:
    days = (wd - ref.weekday()) % 7
    if days == 0:
        days = 7
    return ref + timedelta(days=days)


def _last_weekday(ref: date, wd: int) -> date:
    days = (ref.weekday() - wd) % 7
    if days == 0:
        days = 7
    return ref - timedelta(days=days)


def _parse_terms(text: str) -> list[tuple[int, str]] | None:
    parts = re.split(r"\s*,\s*(?:and\s+)?|\s+and\s+", text.strip())
    result: list[tuple[int, str]] = []
    for part in parts:
        m = _TERM_RE.fullmatch(part.strip())
        if not m:
            return None
        result.append((_to_int(m.group(1)), m.group(2)))
    return result or None


def _parse_absolute(text: str, today: date) -> date | None:
    """Parse explicit date strings like 'December 1st, 2025' or '2025-12-01'."""

    # ISO: 2025-12-01 or 2025/12/01
    m = re.fullmatch(r"(\d{4})[-/](\d{1,2})[-/](\d{1,2})", text)
    if m:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))

    # US numeric: 12/1/2025 or 12-1-2025
    m = re.fullmatch(r"(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})", text)
    if m:
        return date(int(m.group(3)), int(m.group(1)), int(m.group(2)))

    month_names = "|".join(re.escape(w) + r"\.?" for w in sorted(_MONTH_MAP, key=len, reverse=True))
    ordinal_words = "|".join(sorted(_ORDINAL_TO_INT, key=len, reverse=True))
    day_pat = rf"(?:(\d+)(?:st|nd|rd|th)?|({ordinal_words}))"

    def _month_num(s: str) -> int:
        return _MONTH_MAP[s.lower().rstrip(".")]

    # "Month Day, Year" or "Month Day Year" — e.g. "December 1st, 2025" or "Dec. 1, 2025"
    m = re.fullmatch(
        rf"({month_names})\s+{day_pat},?\s*(\d{{4}})?",
        text,
        re.IGNORECASE,
    )
    if m:
        month = _month_num(m.group(1))
        day_num = int(m.group(2)) if m.group(2) else _ORDINAL_TO_INT[m.group(3).lower()]
        year = int(m.group(4)) if m.group(4) else today.year
        return date(year, month, day_num)

    # "Day Month Year" — e.g. "1st December 2025" or "1 December 2025"
    m = re.fullmatch(
        rf"{day_pat}\s+({month_names}),?\s*(\d{{4}})?",
        text,
        re.IGNORECASE,
    )
    if m:
        day_num = int(m.group(1)) if m.group(1) else _ORDINAL_TO_INT[m.group(2).lower()]
        month = _month_num(m.group(3))
        year = int(m.group(4)) if m.group(4) else today.year
        return date(year, month, day_num)

    # "the Nth of Month Year" — e.g. "the 5th of December 2025"
    m = re.fullmatch(
        rf"(?:the\s+)?{day_pat}\s+of\s+({month_names}),?\s*(\d{{4}})?",
        text,
        re.IGNORECASE,
    )
    if m:
        day_num = int(m.group(1)) if m.group(1) else _ORDINAL_TO_INT[m.group(2).lower()]
        month = _month_num(m.group(3))
        year = int(m.group(4)) if m.group(4) else today.year
        return date(year, month, day_num)

    return None


def _parse_impl(text: str, today: date) -> date:
    text = " ".join(text.strip().lower().split())

    # ISO format first — must not be intercepted by any other pattern
    m = re.fullmatch(r"(\d{4})[-/](\d{1,2})[-/](\d{1,2})", text)
    if m:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))

    # Simple anchors
    if text in ("today", "now"):
        return today
    if text == "tomorrow":
        return today + timedelta(days=1)
    if text == "yesterday":
        return today - timedelta(days=1)
    if text in ("day after tomorrow", "the day after tomorrow"):
        return today + timedelta(days=2)
    if text in ("day before yesterday", "the day before yesterday"):
        return today - timedelta(days=2)

    # next/last/this <week|month|year>
    m = re.fullmatch(r"(next|last|this)\s+(week|month|year)", text)
    if m:
        modifier, unit = m.group(1), m.group(2)
        forward = modifier in ("next", "this")
        return _apply_offset(today, 1, unit + "s", forward)

    # next/last/this <weekday>
    m = re.fullmatch(r"(next|last|this)\s+(\w+)", text)
    if m:
        modifier, day_name = m.group(1), m.group(2)
        if day_name in _WEEKDAY_MAP:
            wd = _WEEKDAY_MAP[day_name]
            if modifier == "next":
                return _next_weekday(today, wd)
            if modifier == "last":
                return _last_weekday(today, wd)
            days_diff = (wd - today.weekday()) % 7
            return today + timedelta(days=days_diff)

    # bare weekday → next occurrence
    if text in _WEEKDAY_MAP:
        return _next_weekday(today, _WEEKDAY_MAP[text])

    # "in N units"
    m = re.fullmatch(rf"in\s+({_NUM_PAT})\s+({_UNIT_PAT})", text)
    if m:
        return _apply_offset(today, _to_int(m.group(1)), m.group(2), True)

    # "N units ago"
    m = re.fullmatch(rf"({_NUM_PAT})\s+({_UNIT_PAT})\s+ago", text)
    if m:
        return _apply_offset(today, _to_int(m.group(1)), m.group(2), False)

    # "N units later/hence/from now/from today"
    m = re.fullmatch(
        rf"({_NUM_PAT})\s+({_UNIT_PAT})\s+(?:later|hence|forward)",
        text,
    )
    if m:
        return _apply_offset(today, _to_int(m.group(1)), m.group(2), True)

    # Compound: "{terms} {before|after|from} {base_expr}"
    for direction in ("before", "after", "from"):
        sep = f" {direction} "
        idx = text.find(sep)
        if idx == -1:
            continue
        left = text[:idx].strip()
        right = text[idx + len(sep) :].strip()
        terms = _parse_terms(left)
        if terms is None:
            continue
        try:
            base = _parse_impl(right, today)
        except ValueError:
            continue
        forward = direction in ("after", "from")
        result = base
        for n, unit in terms:
            result = _apply_offset(result, n, unit, forward)
        return result

    # Absolute date
    abs_result = _parse_absolute(text, today)
    if abs_result is not None:
        return abs_result

    raise ValueError(f"Cannot parse date: {text!r}")


def parse(s: str, today: date | None = None) -> date:
    if today is None:
        today = date.today()
    return _parse_impl(s, today)
