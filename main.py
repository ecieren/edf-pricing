import yaml

if __name__ == "__main__":

    filename = "cfg.yaml"
    cfg = yaml.safe_load(open(filename, "r"))

    # ---
    import datetime
    import os
    import pandas as pd

    filename = cfg["tempo_calendar"]["file"]
    start = datetime.datetime.fromisoformat(cfg["tempo_calendar"]["start"])
    end = datetime.datetime.fromisoformat(cfg["tempo_calendar"]["end"])


    # load tempo calendar, check start/end dates (if it exists)
    if os.path.exists(filename):
        tempo = pd.read_csv(filename)
        tempo_start = tempo["date"].min()
        tempo_end = tempo["date"].max()
    else:
        tempo_start = None
        tempo_end = None
    # compare to requested start/end to check if we need to request more data




