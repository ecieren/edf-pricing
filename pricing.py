from idlelib import history
from typing import Dict

import numpy as np
import pandas as pd

import logging_ as logging


def _preproc_history(history: pd.DataFrame):
    # get a sorted copy
    df = history.sort_values(by="date", ignore_index=True)
    # get time-diff in seconds
    dt = df["date"].diff().dt.total_seconds()
    # get consumption in kWh
    df["kWh"] = df["power"] * dt / 3600.0 / 1000
    # put nan if time-delta too big
    df.loc[dt > 6 * 3600, "kWh"] = np.nan
    return df, dt


class Pricing:
    """Class to compute prices at fixed rate."""

    def _init_base(self, cfg: Dict, key: str, power: int):
        self.name = key
        ix = cfg[key]["puissance"].index(power)
        self.subscription = cfg[key]["abonnement"][ix]
        return ix

    def __init__(self, cfg: Dict, key: str, power: int):
        ix = self._init_base(cfg, key, power)
        self.rate = cfg[key]["prix"][ix]

    def _subscription_cost(self, df: pd.DataFrame, dt) -> pd.DataFrame:
        """Compute subscription cost at each time step."""
        # dilution of yearly cost in time
        df["subscription"] = self.subscription * dt / (365 * 24 * 3600)
        # special case in case of leap year (0 since we diluted in 365 days above)
        df.loc[
            np.logical_and(df["date"].dt.month == 2, df["date"].dt.day == 29),
            "subscription",
        ] = 0.0
        return df

    def compute(self, history: pd.DataFrame):

        logging.debug("start")

        # get kWh from history
        df, dt = _preproc_history(history)

        # add subscription cost
        df = self._subscription_cost(df, dt)

        # real time price
        df["price"] = df["kWh"] * self.rate / 100.0

        # total price
        df["price_total"] = df["price"] + df["subscription"]

        return df


class PricingHours(Pricing):
    """Compute prices with hourly rates."""

    def __init__(self, cfg: Dict, key: str, power: int):
        ix = self._init_base(cfg, key, power)
        self.rate_hp = cfg[key]["prix_hp"][ix]
        self.rate_hc = cfg[key]["prix_hc"][ix]

    def compute(self, history):

        logging.debug("start")

        # get kWh from history
        df, dt = _preproc_history(history)

        # add subscription cost
        df = self._subscription_cost(df, dt)

        # real time price
        hc = np.logical_or(df["date"].dt.hour >= 22, df["date"].dt.hour < 6)
        hp = np.logical_not(hc)
        df["price"] = df["kWh"] * (self.rate_hc * hc + self.rate_hp * hp) / 100.0

        # total price
        df["price_total"] = df["price"] + df["subscription"]

        return df


class PricingTempo(Pricing):
    """Compute price with Tempo option."""

    def __init__(self, cfg: Dict, key: str, power: int):
        ix = self._init_base(cfg, key, power)
        self.rate_bleu_hp = cfg[key]["prix_bleu_hp"][ix]
        self.rate_bleu_hc = cfg[key]["prix_bleu_hc"][ix]
        self.rate_blanc_hp = cfg[key]["prix_blanc_hp"][ix]
        self.rate_blanc_hc = cfg[key]["prix_blanc_hc"][ix]
        self.rate_rouge_hp = cfg[key]["prix_rouge_hp"][ix]
        self.rate_rouge_hc = cfg[key]["prix_rouge_hc"][ix]

    def compute(self, history, calendar):

        logging.debug("start")

        # get kWh from history
        df, dt = _preproc_history(history)

        # add subscription cost
        df = self._subscription_cost(df, dt)
        df["realdate"] = df["date"].dt.date

        # sync df with tempo color
        dx = calendar.copy()
        dx["realdate"] = dx["date"].dt.date
        dx.drop(columns=["date", "code"], inplace=True)
        df = pd.merge(df, dx, on="realdate", how="left")
        df.drop(columns=["realdate"], inplace=True)
        del dx

        # real time price
        hc = np.logical_or(df["date"].dt.hour >= 22, df["date"].dt.hour < 6)
        hp = np.logical_not(hc)
        bleu = df["color"] == "Bleu"
        blanc = df["color"] == "Blanc"
        rouge = df["color"] == "Rouge"

        df["price"] = (
            df["kWh"]
            * (
                self.rate_bleu_hc * hc * bleu
                + self.rate_bleu_hp * hp * bleu
                + self.rate_blanc_hc * hc * blanc
                + self.rate_blanc_hp * hp * blanc
                + self.rate_rouge_hc * hc * rouge
                + self.rate_rouge_hp * hp * rouge
            )
            / 100.0
        )

        # total price
        df["price_total"] = df["price"] + df["subscription"]

        return df


if __name__ == "__main__":
    # tmp to test while coding

    p11 = Pricing(cfg["pricing"], "tarif-bleu-base", 9)
    p12 = Pricing(cfg["pricing"], "zen-fixe-base", 9)

    p21 = PricingHours(cfg["pricing"], "tarif-bleu-hc", 9)
    p22 = PricingHours(cfg["pricing"], "zen-fixe-hc", 9)

    p3x = PricingTempo(cfg["pricing"], "tarif-bleu-tempo", 12)

    d11 = p11.compute(history)
    d12 = p12.compute(history)
    d21 = p21.compute(history)
    d22 = p22.compute(history)
    d3x = p3x.compute(history)
