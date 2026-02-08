from datetime import date

import pytest

from app.utils.date import DateRange


class TestDateRange:
    def test_create_valid_range(self):
        dr = DateRange(date(2024, 1, 1), date(2024, 12, 31))
        assert dr.start_date == date(2024, 1, 1)
        assert dr.end_date == date(2024, 12, 31)

    def test_create_same_start_and_end(self):
        dr = DateRange(date(2024, 6, 15), date(2024, 6, 15))
        assert dr.start_date == date(2024, 6, 15)
        assert dr.end_date == date(2024, 6, 15)

    def test_start_after_end_raises_value_error(self):
        with pytest.raises(ValueError, match="start_date must be less than end_date"):
            DateRange(date(2024, 12, 31), date(2024, 1, 1))

    def test_is_tuple(self):
        dr = DateRange(date(2024, 1, 1), date(2024, 12, 31))
        assert isinstance(dr, tuple)
        assert dr[0] == date(2024, 1, 1)
        assert dr[1] == date(2024, 12, 31)

    def test_length(self):
        dr = DateRange(date(2024, 1, 1), date(2024, 12, 31))
        assert len(dr) == 2

    def test_unpacking(self):
        start, end = DateRange(date(2024, 3, 1), date(2024, 3, 31))
        assert start == date(2024, 3, 1)
        assert end == date(2024, 3, 31)
