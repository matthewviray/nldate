from datetime import date

from nldate.parse import parse


def test_today() -> None:
    today = date(2025, 6, 15)
    assert parse("today", today) == today

def test_tommorow() -> None:
    today = date(2025, 6, 15)
    assert parse("tomorrow", today) == date(2025, 6, 16)

def test_yesterday() -> None:
    today = date(2025, 6, 15)
    assert parse("yesterday", today) == date(2025, 6, 14)


def test_absolute_date() -> None:
    today = date(2025, 1, 1)
    assert parse("December 1st, 2025", today) == date(2025, 12, 1)


def test_iso_date() -> None:
    assert parse("2025-03-20") == date(2025, 3, 20)


def test_in_n_days() -> None:
    today = date(2025, 6, 15)
    assert parse("in 5 days", today) == date(2025, 6, 20)


def test_n_weeks_ago() -> None:
    today = date(2025, 6, 15)
    assert parse("3 weeks ago", today) == date(2025, 5, 25)


def test_next_weekday() -> None:
    today = date(2025, 6, 16)  # Monday
    assert parse("next friday", today) == date(2025, 6, 20)


def test_compound_days_before() -> None:
    today = date(2025, 1, 1)
    assert parse("5 days before December 1st, 2025", today) == date(2025, 11, 26)


def test_word_number_offset() -> None:
    today = date(2025, 6, 15)
    assert parse("two weeks from tomorrow", today) == date(2025, 6, 30)

