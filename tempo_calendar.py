import datetime
import os
from typing import Dict

import numpy as np
import pandas as pd
import requests

import logging_ as logging


def period(date: datetime.date) -> str:
    """For a given date return a string representing the period."""
    if date < datetime.date(date.year, 9, 1):
        y = date.year - 1
    else:
        y = date.year
    return f"{y}-{y + 1}"


def get_tempo_colors(period: str) -> pd.DataFrame:
    """Get tempo colors given a period.

    The input period is a str with "YYY1-YYY2" format where YYY2 = YYY1 + 1.
    """

    # api url
    url = f"https://www.api-couleur-tempo.fr/api/joursTempo?periode={period}"

    # request
    logging.info(f"sending request {url}")
    response = requests.get(url)
    response.raise_for_status()

    # check
    if response.status_code != 200:
        logging.error(f"Problem with request {response.status_code}: {response.text}")
        raise ValueError(f"Problem with request !")
    else:
        logging.info(f"got response {response.status_code}")

    # to dataframe
    df = pd.DataFrame(response.json())

    return df


def _format(df: pd.DataFrame) -> pd.DataFrame:
    """Quick formating of DataFrame returned by get_tempo_colors."""

    dg = df.copy()
    # drop "periode" column
    dg.drop(columns=["periode"], inplace=True)
    # change some names
    dg.rename(
        columns={"dateJour": "date", "codeJour": "code", "libClouleur": "color"},
        inplace=True,
    )

    return dg


def _init_calendar(filename: str):
    """Init tempo calendar (overwrite if filename exists)."""

    # get date of the day
    current_date = datetime.datetime.now().date()

    # deduce period
    current_period = period(current_date)

    # log
    logging.debug(
        f"initializing tempo calendar with period {current_period} to {filename}"
    )

    # get data for current period, format
    df = get_tempo_colors(current_period)
    df = _format(df)

    # save to file
    df.to_csv(filename, index=False)


def _fill_missing(cal, start, end) -> pd.DataFrame:

    cal_start = cal["date"].min()
    cal_end = cal["date"].max()

    r1 = pd.date_range(min(start, cal_start), max(end, cal_end))
    r2 = pd.date_range(cal_start, cal_end)

    p1 = np.unique([period(i.date()) for i in r1])
    p2 = np.unique([period(i.date()) for i in r2])

    # get missing data
    df = []
    for p in p1:
        if not p in p2:
            logging.info(f"missing period {p} in calendar")
            df.append(get_tempo_colors(p))
    df = pd.concat(df)
    df = _format(df)
    df["date"] = pd.to_datetime(df["date"])

    # merge with current cal, sort
    df = pd.concat([cal, df])
    df.sort_values(by="date", inplace=True)
    df.drop_duplicates(inplace=True)

    return df


def get(cfg: Dict) -> pd.DataFrame:

    filename = cfg["file"]
    start = datetime.datetime.fromisoformat(cfg["start"])
    end = datetime.datetime.fromisoformat(cfg["end"])

    # load tempo calendar
    logging.info(f"loading tempo calendar")
    if not os.path.exists(filename):
        logging.debug(f"file {filename} not found")
        _init_calendar(filename)
    cal = pd.read_csv(filename)

    # change type to real date and not string
    cal["date"] = pd.to_datetime(cal["date"])

    # get cal start/end dates
    cal_start = cal["date"].min()
    cal_end = cal["date"].max()
    logging.debug(f"current calendar sits between {cal_start} and {cal_end}")

    # fill missing values, save
    logging.debug(f"required dates sits between {start} and {end}")
    if cal_start > start or cal_end < end:
        cal = _fill_missing(cal, start, end)
        cal.to_csv(filename, index=False)
    else:
        logging.debug(f"no missing dates between {cal_start} and {cal_end}")

    # keep only calendar between asked dates
    cal = cal[cal["date"] >= start]
    cal = cal[cal["date"] <= end]

    return cal.reset_index(drop=True)
