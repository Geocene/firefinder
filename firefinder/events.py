import pandas as pd


def group_events(df, *, timestamp_col="timestamp", event_col="event"):
    """
    Convert a boolean event column into start/stop intervals.
    Mirrors the event extraction logic from the original lambda processor.
    """
    df = df.copy()
    df["event_id"] = df[event_col].diff().ne(0).cumsum()
    df_event_starts = df[df[event_col]]
    if df_event_starts.empty:
        return pd.DataFrame()

    events = []
    event_groups = df_event_starts.groupby("event_id")
    for _, group in event_groups:
        start = group[timestamp_col].min()
        last_event = group[timestamp_col].max()
        end = df[df[timestamp_col] > last_event][timestamp_col].min()
        events.append({
            "start_time": start,
            "stop_time": end,
        })

    events_df = pd.DataFrame(events)
    events_df.dropna(subset=["stop_time"], inplace=True)
    if events_df.empty:
        return events_df
    events_df["duration_minutes"] = (
        events_df["stop_time"] - events_df["start_time"]
    ).dt.total_seconds().div(60).astype(int)
    return events_df
