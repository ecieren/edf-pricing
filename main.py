import os
from typing import Dict

import yaml

import consumption
import logging_ as logging
import tempo_calendar


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


if __name__ == "__main__":

    filename = "cfg.yaml"
    cfg = read_cfg(filename)

    logging.init(cfg["logging"])
    logging.info("*** Welcome to edf-pricing ! ***")

    # -- work in progress (1)
    cal = tempo_calendar.get(cfg["tempo_calendar"])

    # -- work in progress (2)
    cns = consumption.read(cfg["consumption"])

    # -- end ------------------------------------------------------------------
    logging.info("*** Edf-pricing over, goodbye ! ***")
    logging.finalize()
