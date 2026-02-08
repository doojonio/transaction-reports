from pathlib import Path

from pandas import DataFrame, read_csv  # type: ignore[import-untyped]

from app.settings import settings


def get_user_countries() -> DataFrame:
    """
    Get user countries from CSV file.

    Returns:
        DataFrame with user countries.
    """
    file_path = Path(settings.PROJECT_ROOT) / "shared" / "external" / "user_country.csv"
    df = read_csv(file_path, delimiter=";")
    df.columns = ["id", "country"]
    return df
