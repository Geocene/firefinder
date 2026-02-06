from .detector import (
    fire_detector_v2,
    find_raw_events,
    smooth_events,
    remove_low_temp_event,
    remove_low_temp_delta_event,
    compute_corrected_value,
)
from .preprocess import (
    prepare_timeseries,
    filter_sensor_data,
    DEFAULT_SENSORS,
    SENTINEL_VALUE,
)
from .events import events_from_boolean

__all__ = [
    "fire_detector_v2",
    "find_raw_events",
    "smooth_events",
    "remove_low_temp_event",
    "remove_low_temp_delta_event",
    "compute_corrected_value",
    "prepare_timeseries",
    "filter_sensor_data",
    "DEFAULT_SENSORS",
    "SENTINEL_VALUE",
    "events_from_boolean",
]

__version__ = "0.1.0"
