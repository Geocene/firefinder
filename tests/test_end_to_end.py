from pathlib import Path

import pandas as pd

from firefinder import prepare_timeseries, fire_detector_v2, group_events

DATA_PATH = Path(__file__).resolve().parent / "data.json"
PARAMETERS = {
    "primary_threshold": 5,
    "min_event_sec": 900,
    "fall_rate": 1 / 500,
    "rise_rate": 2,
    "correction": "true",
    "min_event_temp_delta": 10,
    "min_event_temp": 15,
    "min_break_sec": 1200,
}


def test_end_to_end_events_from_json():
    df = pd.read_json(DATA_PATH)

    # data.json stores timestamps as epoch milliseconds
    if pd.api.types.is_integer_dtype(df["timestamp"]) or pd.api.types.is_float_dtype(df["timestamp"]):
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True, errors="coerce")

    prepared = prepare_timeseries(df, correction="true")
    out = fire_detector_v2(prepared, **PARAMETERS)
    events = group_events(out)

    # there should be 161 events in the test data
    assert len(events) == 161
