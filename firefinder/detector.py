import numpy as np
import pandas as pd

MINIMUM_EVENT_GAP = 1800  # seconds
MINIMUM_EVENT_DURATION = 1200  # seconds
PRIMARY_THRESHOLD = 30
LOOKBACK_DURATION = 5  # minutes
RISE_RATE = 2  # degrees per minute
FALL_RATE = 1 / 500  # degrees per degree of stove temperature


def fire_detector_v2(df, **kwargs):
    df = find_raw_events(df, **kwargs)
    df = smooth_events(df, **kwargs)
    df = remove_low_temp_event(df, **kwargs)
    df = remove_low_temp_delta_event(df, **kwargs)
    return df


def find_raw_events(
    df,
    primary_threshold=PRIMARY_THRESHOLD,
    min_event_sec=MINIMUM_EVENT_DURATION,
    fall_rate=FALL_RATE,
    rise_rate=RISE_RATE,
    correction="false",
    **kwargs,
):
    primary_threshold = float(primary_threshold)
    min_event_sec = float(min_event_sec)
    fall_rate = float(fall_rate)
    rise_rate = float(rise_rate)
    df = compute_corrected_value(df, correction)
    df = df.set_index("timestamp")
    sample_interval = df.index.to_series().diff().dt.total_seconds().div(60).median()
    samples = max(1, round(LOOKBACK_DURATION / sample_interval))
    df["value_lag"] = df["value"].shift(samples)
    df["temp_diff_5min"] = df["value"] - df["value_lag"]
    df["temp_diff_5min"] = df["temp_diff_5min"].fillna(0) / sample_interval

    window = min(100, round(min_event_sec / (60 * sample_interval)))
    df["q80"] = df["temp_diff_5min"].rolling(window, min_periods=1).quantile(0.8)

    df["event"] = False
    df.loc[df["value"] > primary_threshold, "event"] = True
    df.loc[df["q80"] <= 0, "event"] = False
    df.loc[df["temp_diff_5min"] >= rise_rate, "event"] = True
    df.loc[df["temp_diff_5min"] < -1 * df["value"] * fall_rate, "event"] = False
    df["difftimes"] = df.index.to_series().diff().dt.total_seconds().fillna(0)
    df.loc[df["difftimes"] > (sample_interval * 60), "event"] = False
    df.reset_index(inplace=True)
    return df[["timestamp", "value", "event"]]


def compute_corrected_value(df, correction, ambient_default=20.0):
    """
    Subtracts ambient temperature from stove readings.
    If an ambient sensor_type_id (9) is present, uses time-aligned ambient values.
    Otherwise, subtracts a constant default ambient.
    """
    if not _is_true(correction):
        return df

    df = df.copy()
    df["sensor"] = df["sensor_type_id"].map({1: "stove", 9: "ambient"})

    if "ambient" in df["sensor"].values:
        stove = (
            df[df["sensor"] == "stove"][["mission_id", "timestamp", "value"]]
            .rename(columns={"value": "stove"})
        )
        ambient = (
            df[df["sensor"] == "ambient"][["mission_id", "timestamp", "value"]]
            .rename(columns={"value": "ambient"})
        )
        out = pd.merge(stove, ambient, on=["mission_id", "timestamp"], how="left")
        out["value"] = out["stove"] - out["ambient"]
        return (
            out[["mission_id", "timestamp", "value"]]
            .sort_values("timestamp")
            .reset_index(drop=True)
        )
    else:
        out = df[df["sensor"] == "stove"][["mission_id", "timestamp", "value"]].copy()
        out["value"] = out["value"] - ambient_default
        return out.sort_values("timestamp").reset_index(drop=True)


def remove_low_temp_delta_event(df, min_event_temp_delta=None, **kwargs):
    """
    Removes events whose intra-event temperature range is below the threshold.
    """
    if min_event_temp_delta is None or min_event_temp_delta == "":
        return df

    df = df.copy()
    df["event_id"] = df["event"].diff().ne(0).cumsum()
    event_max = df.groupby("event_id")["value"].transform("max")
    event_min = df.groupby("event_id")["value"].transform("min")
    temp_delta = event_max - event_min

    df["event"] = np.where(temp_delta < float(min_event_temp_delta), False, df["event"])
    df.drop(columns=["event_id"], inplace=True)
    return df


def remove_low_temp_event(df, min_event_temp=None, **kwargs):
    if min_event_temp is None or min_event_temp == "":
        return df
    df["event_id"] = df["event"].diff().ne(0).cumsum()
    event_max_temp = df.groupby("event_id")["value"].transform("max")
    df["event_max"] = event_max_temp
    df["event"] = np.where(df["event_max"] < float(min_event_temp), False, df["event"])
    df.drop(columns=["event_id", "event_max"], inplace=True)
    return df


def smooth_events(df, **kwargs):
    df = apply_noise_correction(df, is_non_event_short_gap, **kwargs)
    df = apply_noise_correction(df, is_event_short_duration, **kwargs)
    return df


def apply_noise_correction(df, condition: callable, **kwargs):
    """
    Applies corrections to the DataFrame based on a provided condition function.
    The condition function should take a group as input and return a boolean.
    """
    sample_interval = df["timestamp"].diff().dt.total_seconds().median()
    df["event_change"] = df["event"].astype(int).diff().ne(0).cumsum()
    event_groups = df.groupby("event_change")

    for _, group in event_groups:
        if condition(group, sample_interval, **kwargs):
            df.loc[group.index, "event"] = not group["event"].iloc[0]

    df.drop("event_change", axis=1, inplace=True)
    return df


def is_non_event_short_gap(group, sample_interval, min_break_sec=MINIMUM_EVENT_GAP, **kwargs):
    """Check if the group represents a non-event short gap."""
    return (not group["event"].iloc[0]) and len(group) * sample_interval < float(min_break_sec)


def is_event_short_duration(group, sample_interval, min_event_sec=MINIMUM_EVENT_DURATION, **kwargs):
    """Check if the group represents a event of short duration."""
    return group["event"].iloc[0] and len(group) * sample_interval < float(min_event_sec)


def _is_true(value):
    if isinstance(value, str):
        return value.lower() == "true"
    return bool(value)
