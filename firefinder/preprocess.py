import numpy as np
import pandas as pd

DEFAULT_SENSORS = {
    1: "stove",
    2: "stove",
    3: "stove",
    4: "stove",
    9: "ambient",
}

SENTINEL_VALUE = 983  # thermocouple broken value


def prepare_timeseries(
    df,
    *,
    timestamp_col="timestamp",
    value_col="value",
    sensor_col="sensor_type_id",
    correction="false",
    sensor="stove",
    sensors=DEFAULT_SENSORS,
    sentinel_value=SENTINEL_VALUE,
):
    """
    Prepare a timeseries DataFrame for FireFinder+.
    Mirrors the cleaning done in the original lambda processor.
    """
    df = df.copy()
    df[timestamp_col] = pd.to_datetime(df[timestamp_col], utc=True)
    df[value_col] = pd.to_numeric(df[value_col])
    df.sort_values(by=timestamp_col, inplace=True)
    df.dropna(subset=[timestamp_col], inplace=True)
    df[value_col] = df[value_col].replace(sentinel_value, np.nan)
    df = filter_sensor_data(
        df,
        sensor=sensor,
        correction=correction,
        sensor_col=sensor_col,
        sensors=sensors,
    )
    return df


def filter_sensor_data(
    df,
    *,
    sensor="stove",
    correction="false",
    sensor_col="sensor_type_id",
    sensors=DEFAULT_SENSORS,
):
    """
    Filters the DataFrame to include only rows for the specified sensor type.
    If correction is True, include all sensors for correction purposes.
    """
    if _is_true(correction):
        return df
    sensor_ids = [sensor_id for sensor_id, label in sensors.items() if label == sensor]
    return df[df[sensor_col].isin(sensor_ids)]


def _is_true(value):
    if isinstance(value, str):
        return value.lower() == "true"
    return bool(value)
