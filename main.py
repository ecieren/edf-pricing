import os
from typing import Dict

import yaml

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

    return cfg


if __name__ == "__main__":

    filename = "cfg.yaml"
    cfg_ = read_cfg(filename)

    logging.init(cfg_["logging"])
    logging.info("*** Welcome to edf-pricing ! ***")

    # -- work in progress
    cfg = cfg_["tempo_calendar"]
    cal = tempo_calendar.get(cfg_["tempo_calendar"])

    # -- end ------------------------------------------------------------------
    logging.info("*** Edf-pricing over, goodbye ! ***")
    logging.finalize()
