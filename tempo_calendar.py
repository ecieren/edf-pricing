from typing import List
import requests
import pandas as pd
import datetime


def period(date: datetime.date) -> str:
    """For a given date return a string representing the period."""
    if date < datetime.date(date.year, 9, 1):
        y = date.year - 1
    else:
        y = date.year
    return f"{y}-{y + 1}"

def get_tempo_colors(periode:str) ->pd.DataFrame:
    """Get tempo colors given a period.

    The period is a strint with "YYY1-YYY2" format where YYY2 = YYY1 + 1.
    """
    url = f"https://www.api-couleur-tempo.fr/api/joursTempo?periode={periode}"

    response = requests.get(url)
    response.raise_for_status()

    if response.status_code != 200:
        raise ValueError(f"Problem with request {response.status_code}: {response.text}")

    df = pd.DataFrame(response.json())

    return df

def _format_calendar(df: pd.DataFrame) -> pd.DataFrame:

    dg = df.copy()

    dg.drop(columns=["periode"], inplace=True)
    dg.rename(columns={"dateJour":"date", "codeJour":"code", "libClouleur":"color"}, inplace=True)
    dg["date"] = pd.to_datetime(dg["date"])

    return dg


def init_calendar(filename:str):




    pass



# Test
if __name__ == "__main__":

    # dg = get_tempo_colors("2024-2025")
    dg2 = format_calendar(dg)

