from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

from app.services.user_countries import get_user_countries


class TestGetUserCountries:
    def test_returns_dataframe(self):
        df = get_user_countries()
        assert isinstance(df, pd.DataFrame)

    def test_has_correct_columns(self):
        df = get_user_countries()
        assert list(df.columns) == ["id", "country"]

    def test_dataframe_not_empty(self):
        df = get_user_countries()
        assert len(df) > 0

    def test_id_column_contains_integers(self):
        df = get_user_countries()
        assert df["id"].dtype in [int, "int64", "Int64"]

    def test_country_column_contains_strings(self):
        df = get_user_countries()
        dtype_str = str(df["country"].dtype)
        assert df["country"].dtype == object or "str" in dtype_str.lower()

    def test_no_null_values(self):
        df = get_user_countries()
        assert not df["id"].isnull().any()
        assert not df["country"].isnull().any()

    def test_specific_user_countries(self):
        df = get_user_countries()
        assert df[df["id"] == 1]["country"].values[0] == "Germany"
        assert df[df["id"] == 2]["country"].values[0] == "Canada"
        assert df[df["id"] == 3]["country"].values[0] == "France"

    def test_file_path_construction(self):
        with patch("app.services.user_countries.read_csv") as mock_read_csv:
            mock_read_csv.return_value = pd.DataFrame({"user_id": [1], "country": ["Test"]})

            get_user_countries()

            call_args = mock_read_csv.call_args
            file_path = call_args[0][0]
            assert isinstance(file_path, Path)
            assert str(file_path).endswith("shared/external/user_country.csv")

    def test_uses_semicolon_delimiter(self):
        with patch("app.services.user_countries.read_csv") as mock_read_csv:
            mock_read_csv.return_value = pd.DataFrame({"user_id": [1], "country": ["Test"]})

            get_user_countries()

            assert mock_read_csv.call_args[1]["delimiter"] == ";"

    def test_file_not_found_raises_error(self):
        with patch("app.services.user_countries.Path") as mock_path:
            mock_path.return_value.__truediv__.return_value.__truediv__.return_value.__truediv__.return_value = Path(
                "/nonexistent/path.csv"
            )

            with pytest.raises(FileNotFoundError):
                get_user_countries()
