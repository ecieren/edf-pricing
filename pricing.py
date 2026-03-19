from typing import Dict

import numpy as np
import pandas as pd


def _preproc_history(history: pd.DataFrame):
    # get a sorted copy
    df = history.sort_values(by="date", ignore_index=True)
    # get time-diff in seconds
    dt = df["date"].diff().dt.total_seconds()
    # get consumption in kWh
    df["kWh"] = df["power"] * dt / 3600.0 / 1000
    return df, dt


class Pricing:

    def _init_base(self, cfg: Dict, key: str, power: int):
        self.name = key
        ix = cfg[key]["puissance"].index(power)
        self.abo = cfg[key]["abonnement"][ix]
        return ix

    def __init__(self, cfg: Dict, key: str, power: int):
        ix = self._init_base(cfg, key, power)
        self.rate = cfg[key]["prix"][ix]

    def _abo_cost(self, df: pd.DataFrame, dt) -> pd.DataFrame:
        """Compute subscription cost at each time step."""
        # dilution of yearly cost in time
        df["abo"] = self.abo * dt / (365 * 24 * 3600)
        # special case in case of leap year (0 since we diluted in 365 days above)
        df.loc[
            np.logical_and(df["date"].dt.month == 2, df["date"].dt.day == 29), "abo"
        ] = 0.0
        return df

    def compute(self, history: pd.DataFrame):
        # get kWh from history
        df, dt = _preproc_history(history)

        # add subscription cost
        df = self._abo_cost(df, dt)

        # real time price
        df["price"] = df["kWh"] * self.rate / 100.0

        # total price
        df["price_total"] = df["price"] + df["abo"]

        return df


class PricingHours(Pricing):
    def __init__(self, cfg: Dict, key: str, power: int):
        ix = self._init_base(cfg, key, power)
        self.rate_hp = cfg[key]["prix_hp"][ix]
        self.rate_hc = cfg[key]["prix_hc"][ix]

    def compute(self, history):
        pass


class PricingTempo(Pricing):
    def __init__(self, cfg: Dict, key: str, power: int):
        ix = self._init_base(cfg, key, power)
        self.rate_bleu_hp = cfg[key]["prix_bleu_hp"][ix]
        self.rate_bleu_hc = cfg[key]["prix_bleu_hc"][ix]
        self.rate_blanc_hp = cfg[key]["prix_blanc_hp"][ix]
        self.rate_blanc_hc = cfg[key]["prix_blanc_hc"][ix]
        self.rate_rouge_hp = cfg[key]["prix_rouge_hp"][ix]
        self.rate_rouge_hc = cfg[key]["prix_rouge_hc"][ix]

    def compute(self, history):
        pass


if __name__ == "__main__":
    # tmp to test while coding

    p1 = Pricing(cfg["pricing"], "tarif-bleu-base", 9)
    p2 = Pricing(cfg["pricing"], "zen-fixe-base", 9)

    # p2 = PricingHours(cfg["pricing"], "zen-fixe-base-hc", 12)
    # p3 = PricingTempo(cfg["pricing"], "tarif-bleu-tempo", 12)

    d1 = p1.compute(cns)
    d2 = p2.compute(cns)
