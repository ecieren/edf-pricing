import datetime
from typing import Dict

import numpy as np
import pandas as pd


def read(cfg: Dict) -> pd.DataFrame:

    df = pd.read_csv(
        cfg["file"],
        encoding=cfg["encoding"],
        sep=cfg["sep"],
        skiprows=cfg["skiprows"],
    )

    # rename columns
    df.rename(
        columns={
            "Date et heure de relève par le distributeur": "date",
            "Puissance atteinte (W)": "power",
            "Nature de la donnée": "nature",
        },
        inplace=True,
    )
    df.drop(columns="nature", inplace=True)
    df.reset_index(drop=True, inplace=True)

    # find indexes with date
    ix = np.where(df["power"].isna())[0]
    iy = []
    for i in ix:
        try:
            datetime.datetime.strptime(df.loc[i, "date"], "%d/%m/%Y")
            iy.append(i)
        except ValueError:
            pass

    def chngstr(s: str) -> str:
        date = datetime.datetime.strptime(s, "%d/%m/%Y")
        return f"{date.year:04d}-{date.month:02d}-{date.day:02d}"

    # go through all indexes, change time with datetime
    i = iy[0]
    date = chngstr(df["date"].iloc[i])
    while i < len(df) - 1:
        i += 1
        if i in iy:
            date = chngstr(df["date"].iloc[i])
        else:
            df.iloc[i, 0] = date + " " + df["date"].iloc[i]

    # drop
    df.drop(index=iy, inplace=True)
    df["date"] = pd.to_datetime(df["date"])
    df.sort_values(by=["date"], inplace=True)
    df.reset_index(drop=True, inplace=True)

    return df
