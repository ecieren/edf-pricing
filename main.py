import datetime
import os
from typing import Dict

import yaml

import consumption
import logging_ as logging
import tempo_calendar
from pricing import Pricing, PricingHours, PricingTempo


def read_cfg(filename: str) -> Dict:
    """Read and process config file."""

    # read file
    cfg = yaml.safe_load(open(filename, "r"))

    # create dirs
    if not os.path.isdir(cfg["app"]["data_dir"]):
        os.mkdir(cfg["app"]["data_dir"])

    # adjust path to current os
    cfg["tempo_calendar"]["file"] = os.path.join(*cfg["tempo_calendar"]["file"])
    cfg["consumption"]["file"] = os.path.join(*cfg["consumption"]["file"])

    # set default args
    cfg_ = cfg["consumption"]
    for k in ["encoding", "sep", "skiprows"]:
        if k not in cfg_:
            cfg_[k] = None

    return cfg


def print_bloc(p, d):
    days = (d["date"].max() - d["date"].min()).total_seconds() / (3600 * 24)
    print(
        f"  {p.name:16} : "
        f"subscription {d["subscription"].sum()/days:.2f} €/day; "
        f"consumption {d["kWh"].sum()/days:.1f} kWh/day "
        f"{d["price"].sum()/days:.2f} €/day; "
        f"total {d["price_total"].sum()/days:.2f} €/day"
    )


def run_study(cfg, history, calendar):

    # compute price with all options
    p11 = Pricing(cfg["pricing"], "tarif-bleu-base", 9)
    p12 = Pricing(cfg["pricing"], "zen-fixe-base", 9)
    p21 = PricingHours(cfg["pricing"], "tarif-bleu-hc", 9)
    p22 = PricingHours(cfg["pricing"], "zen-fixe-hc", 9)
    p3x = PricingTempo(cfg["pricing"], "tarif-bleu-tempo", 12)

    d11 = p11.compute(history)
    d12 = p12.compute(history)
    d21 = p21.compute(history)
    d22 = p22.compute(history)
    d3x = p3x.compute(history, calendar)

    print("ON ALL HISTORY :")
    for p, d in zip([p11, p12, p21, p22, p3x], [d11, d12, d21, d22, d3x]):
        print_bloc(p, d)
    print()

    print("LAST FULL YEAR :")
    y = datetime.datetime.now().year - 1
    li = [d[d["date"].dt.year == y] for d in [d11, d12, d21, d22, d3x]]
    for p, d in zip([p11, p12, p21, p22, p3x], li):
        print_bloc(p, d)
    print()

    print("LAST 365 DAYS :")
    ts = d11["date"].max() - datetime.timedelta(days=365)
    li = [d[d["date"] >= ts] for d in [d11, d12, d21, d22, d3x]]
    for p, d in zip([p11, p12, p21, p22, p3x], li):
        print_bloc(p, d)


if __name__ == "__main__":

    filename = "cfg.yaml"
    cfg = read_cfg(filename)

    logging.init(cfg["logging"])
    logging.info("*** Welcome to edf-pricing ! ***")

    # -- work in progress

    # get tempo calendar, read history
    calendar = tempo_calendar.get(cfg["tempo_calendar"])
    history = consumption.read(cfg["consumption"])
    run_study(cfg, history, calendar)

    # -- end ------------------------------------------------------------------
    logging.info("*** Edf-pricing over, goodbye ! ***")
    logging.finalize()
