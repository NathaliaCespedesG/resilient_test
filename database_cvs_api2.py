import os
import math
import numpy as np
import pandas as pd
import requests

from datetime import datetime
from dateutil import parser, relativedelta
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from concurrent.futures import ThreadPoolExecutor, as_completed


# =========================
# HTTP Session (fast + stable)
# =========================
def make_session(pool_maxsize=50):
    s = requests.Session()
    retries = Retry(
        total=5,
        backoff_factor=0.3,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET", "POST"),
        raise_on_status=False
    )
    adapter = HTTPAdapter(max_retries=retries, pool_connections=pool_maxsize, pool_maxsize=pool_maxsize)
    s.mount("http://", adapter)
    s.mount("https://", adapter)
    return s


# =========================
# Helpers
# =========================
def nan_to_none_df(df: pd.DataFrame) -> pd.DataFrame:
    """Convert NaNs to None for JSON serialization."""
    return df.replace({np.nan: None})


def safe_date_to_yyyy_mm_dd(series: pd.Series, strip_last6=False) -> pd.Series:
    """Vectorized date parsing to YYYY-MM-DD. If strip_last6=True, trims timezone suffix like '...+00:00'."""
    if strip_last6:
        s = series.astype(str).str[:-6]
    else:
        s = series.astype(str)

    dt = pd.to_datetime(s, errors="coerce")
    return dt.dt.strftime("%Y-%m-%d")


def post_rows_threaded(session, url, rows, max_workers=12, timeout=30):
    """POST many rows to a single-row endpoint using threads (I/O bound)."""
    def _post(row):
        r = session.post(url, json=row, timeout=timeout)
        return r.status_code, r.text

    bad = []
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futs = [ex.submit(_post, row) for row in rows]
        for f in as_completed(futs):
            status, text = f.result()
            if status not in (200, 201):
                bad.append((status, text))
    return bad


def post_rows_bulk_or_threaded(session, url, rows, use_bulk=True, bulk_suffix="/bulk/", max_workers=12, timeout=60):
    """
    If use_bulk=True tries POST to url + '/bulk/' with payload {"items": [...]} or just [...],
    otherwise posts row-by-row with threads.
    """
    if not rows:
        return []

    if use_bulk:
        bulk_url = url.rstrip("/") + bulk_suffix
        # Try two common payload formats:
        for payload in (rows, {"items": rows}):
            r = session.post(bulk_url, json=payload, timeout=timeout)
            if r.status_code in (200, 201):
                return []
        # If bulk failed, fall back
        print(f"[WARN] Bulk failed for {bulk_url}. Falling back to threaded single-row POSTs.")

    return post_rows_threaded(session, url, rows, max_workers=max_workers, timeout=timeout)


# =========================
# Main class
# =========================
class DatabaseServer_csv:
    def __init__(self, path=None, base_url="http://127.0.0.1:8000", pool_maxsize=50):
        self.users_path = path
        self.base_url = base_url.rstrip("/")
        self.session = make_session(pool_maxsize=pool_maxsize)

        self.user_data = {}
        self.id_available = []

    # -------------------------
    # USERS
    # -------------------------
    def get_users(self):
        url = f"{self.base_url}/api/users"
        r = self.session.get(url, timeout=30)
        if r.status_code != 200:
            raise RuntimeError(f"GET users failed: {r.status_code} {r.text}")

        data = r.json()
        self.user_data = {u["username"]: u for u in data["users"]}
        self.id_available = list(self.user_data.keys())
        print(f"[OK] Loaded {len(self.id_available)} users.")

    def extract_user_data(self, username):
        user = self.user_data.get(username)
        if user:
            return user["id"], user["scale_device"], user["scanwatch_device"], user["sleepmat_device"]
        return None, None, None, None

    # -------------------------
    # Utility: safer date parsing for your old helper
    # -------------------------
    def convert_to_yyyy_mm_dd(self, date_string):
        """Return YYYY-MM-DD or None."""
        if date_string is None:
            return None
        if isinstance(date_string, float) and np.isnan(date_string):
            return None
        if isinstance(date_string, str) and date_string.strip().lower() == "nan":
            return None

        try:
            dt = datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            try:
                dt = datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%S")
            except ValueError:
                try:
                    dt = parser.parse(date_string)
                except Exception:
                    return None
        return dt.strftime("%Y-%m-%d")

    # -------------------------
    # SCANWATCH SUMMARY (FAST)
    # -------------------------
    def upload_scanwatch_summary_data(self, chunksize=5000, use_bulk=True, max_workers=12):
        url = f"{self.base_url}/api/scanwatches/summary/"
        for username in self.id_available:
            path = f"/home/nathalia/Withings_ScanWatch/Withings_ScanWatch/db/General/{username}/ScanWatch_summary.csv"
            user_id, _, watch_id, _ = self.extract_user_data(username)

            if watch_id is None or not os.path.exists(path):
                continue

            for chunk in pd.read_csv(path, chunksize=chunksize):
                # Expected columns
                # date, HR_Average, Calories, Steps, HR_max, HR_min
                if "date" not in chunk.columns:
                    continue

                chunk["date"] = safe_date_to_yyyy_mm_dd(chunk["date"], strip_last6=True)

                for c in ["HR_Average", "Calories", "Steps", "HR_max", "HR_min"]:
                    if c in chunk.columns:
                        chunk[c] = pd.to_numeric(chunk[c], errors="coerce")

                chunk["device"] = watch_id
                chunk["user"] = user_id

                # Rename to API fields
                mapping = {
                    "HR_Average": "average_heart_rate",
                    "Calories": "calories",
                    "Steps": "steps",
                    "HR_max": "hr_max",
                    "HR_min": "hr_min",
                }
                chunk = chunk.rename(columns=mapping)

                # Keep only the API fields that exist
                keep = ["device", "user", "date", "average_heart_rate", "calories", "steps", "hr_max", "hr_min"]
                keep = [k for k in keep if k in chunk.columns]
                chunk = chunk[keep]

                records = nan_to_none_df(chunk).to_dict("records")
                bad = post_rows_bulk_or_threaded(
                    self.session, url, records, use_bulk=use_bulk, max_workers=max_workers
                )
                if bad:
                    print(f"[WARN] {username} scanwatch summary: {len(bad)} failed rows. First 2: {bad[:2]}")

            print(f"[OK] ScanWatch summary uploaded for {username}")

    # -------------------------
    # SLEEPMAT SUMMARY (FAST)
    # -------------------------
    def upload_sleep_summary_data(self, chunksize=2000, use_bulk=True, max_workers=12):
        url = f"{self.base_url}/api/sleepmats/summary/"

        for username in self.id_available:
            path = f"/home/nathalia/Withings_ScanWatch/Withings_ScanWatch/db/General/{username}/SleepMat_summary.csv"
            user_id, _, _, sleep_id = self.extract_user_data(username)

            if sleep_id is None or not os.path.exists(path):
                continue

            for chunk in pd.read_csv(path, chunksize=chunksize):
                # date field
                if "date" in chunk.columns:
                    # your original used: dict[j]['date'][:-6] and format %Y-%m-%dT%H:%M:%S
                    chunk["date"] = safe_date_to_yyyy_mm_dd(chunk["date"], strip_last6=True)

                # Parse start/end as ISO
                for c in ["start_date", "end_date"]:
                    if c in chunk.columns:
                        dt = pd.to_datetime(chunk[c], errors="coerce")
                        chunk[c] = dt.dt.tz_localize(None).dt.strftime("%Y-%m-%dT%H:%M:%S")

                # hr_date fields (messy in your code)
                # We'll coerce to YYYY-MM-DD
                if "date_hr_sleep_ap" in chunk.columns:
                    chunk["hr_date_af"] = safe_date_to_yyyy_mm_dd(chunk["date_hr_sleep_ap"], strip_last6=False)
                else:
                    chunk["hr_date_af"] = None

                if "date_rr_sleep_ap" in chunk.columns:
                    chunk["hr_date_rr"] = safe_date_to_yyyy_mm_dd(chunk["date_rr_sleep_ap"], strip_last6=False)
                else:
                    chunk["hr_date_rr"] = None

                # numeric columns: coerce quickly
                numeric_cols = [
                    "Breathing disturbances", "Deep sleep duration", "Duration to sleep", "Duration to wakeup",
                    "HR average", "Light sleep duration", "Rem sleep duration", "RR average", "Sleep score",
                    "Wake up count", "Wake up duration", "Total sleep time", "Total time in bed", "Awake in bed",
                    "Apnea", "Out of bed count", "hr_sleep_ap", "rr_sleep_ap", "RR max", "RR min", "HR max", "HR min",
                    "Snoring episodes", "Snoring time"
                ]
                for c in numeric_cols:
                    if c in chunk.columns:
                        chunk[c] = pd.to_numeric(chunk[c], errors="coerce")

                chunk["device"] = sleep_id
                chunk["user"] = user_id

                mapping = {
                    "Breathing disturbances": "breathing_disturbances",
                    "Deep sleep duration": "deep_sleep_duration",
                    "Duration to sleep": "duration_to_sleep",
                    "Duration to wakeup": "duration_to_wakeup",
                    "HR average": "average_heart_rate",
                    "Light sleep duration": "light_sleep_duration",
                    "Rem sleep duration": "rem_sleep_duration",
                    "RR average": "average_rr",
                    "Sleep score": "sleep_score",
                    "Wake up count": "wakeup_count",
                    "Wake up duration": "wakeup_duration",
                    "Total sleep time": "total_sleep_time",
                    "Total time in bed": "total_time_in_bed",
                    "Awake in bed": "awake_in_bed",
                    "Apnea": "apnea",
                    "Out of bed count": "out_of_bed_count",
                    "hr_sleep_ap": "hr_af",
                    "rr_sleep_ap": "hr_rr",  # NOTE: your naming was confusing; adjust if needed
                    "RR max": "rr_max",
                    "RR min": "rr_min",
                    "HR max": "hr_max",
                    "HR min": "hr_min",
                    "Snoring episodes": "snoring_episodes",
                    "Snoring time": "snoring_time",
                }
                chunk = chunk.rename(columns=mapping)

                keep = [
                    "device", "user", "date",
                    "breathing_disturbances", "deep_sleep_duration", "duration_to_sleep", "duration_to_wakeup",
                    "average_heart_rate", "light_sleep_duration", "rem_sleep_duration", "average_rr", "sleep_score",
                    "wakeup_count", "wakeup_duration", "total_sleep_time", "total_time_in_bed", "awake_in_bed",
                    "apnea", "out_of_bed_count",
                    "start_date", "end_date",
                    "hr_date_af", "hr_date_rr",
                    "hr_af", "hr_rr",
                    "hr_max", "hr_min", "rr_max", "rr_min",
                    "snoring_episodes", "snoring_time"
                ]
                keep = [k for k in keep if k in chunk.columns]
                chunk = chunk[keep]

                records = nan_to_none_df(chunk).to_dict("records")
                bad = post_rows_bulk_or_threaded(
                    self.session, url, records, use_bulk=use_bulk, max_workers=max_workers
                )
                if bad:
                    print(f"[WARN] {username} sleep summary: {len(bad)} failed rows. First 2: {bad[:2]}")

            print(f"[OK] Sleep summary uploaded for {username}")

    # -------------------------
    # INTRA SCANWATCH (FAST)
    # -------------------------
    def upload_intra_scanwatch_summary_data(self, chunksize=10000, use_bulk=True, max_workers=12):
        url = f"{self.base_url}/api/scanwatches/intra_activity/"
        ids_sorted = sorted(self.id_available)

        for username in ids_sorted:
            path = f"/home/nathalia/Withings_ScanWatch/Withings_ScanWatch/db/General/{username}/ScanWatch_intra_activity.csv"
            user_id, _, watch_id, _ = self.extract_user_data(username)

            if watch_id is None or not os.path.exists(path):
                continue

            for chunk in pd.read_csv(path, chunksize=chunksize):
                # Expected columns: Heart Rate, date HR, Steps, date Steps, Calories, date Calories
                cols = ["Heart Rate", "date HR", "Steps", "date Steps", "Calories", "date Calories"]
                existing = [c for c in cols if c in chunk.columns]
                chunk = chunk[existing]

                for c in existing:
                    chunk[c] = pd.to_numeric(chunk[c], errors="coerce")

                chunk["user"] = user_id
                chunk["device"] = watch_id

                chunk = chunk.rename(columns={
                    "Heart Rate": "heart_rate",
                    "date HR": "date_heart_rate",
                    "Steps": "steps",
                    "date Steps": "date_steps",
                    "Calories": "calories",
                    "date Calories": "date_calories",
                })

                keep = ["user", "device", "heart_rate", "date_heart_rate", "steps", "date_steps", "calories", "date_calories"]
                keep = [k for k in keep if k in chunk.columns]
                chunk = chunk[keep]

                records = nan_to_none_df(chunk).to_dict("records")
                bad = post_rows_bulk_or_threaded(
                    self.session, url, records, use_bulk=use_bulk, max_workers=max_workers
                )
                if bad:
                    print(f"[WARN] {username} intra scanwatch: {len(bad)} failed rows. First 2: {bad[:2]}")

            print(f"[OK] Intra ScanWatch uploaded for {username}")

    # -------------------------
    # INTRA SLEEPMAT (FAST)
    # -------------------------
    def upload_intra_sleep_summary_data(self, chunksize=10000, use_bulk=True, max_workers=12):
        url = f"{self.base_url}/api/sleepmats/intraactivity/"
        ids_sorted = sorted(self.id_available)

        for username in ids_sorted:
            path = f"/home/nathalia/Withings_ScanWatch/Withings_ScanWatch/db/General/{username}/Sleepmat_intra_activity.csv"
            user_id, _, _, sleep_id = self.extract_user_data(username)

            if sleep_id is None or not os.path.exists(path):
                continue

            for chunk in pd.read_csv(path, chunksize=chunksize):
                cols = [
                    "startdate", "enddate", "Sleep state",
                    "Heart Rate date", "Heart Rate",
                    "Respiration rate date", "Respiration rate",
                    "Snoring date", "Snoring",
                    "sdnn_1 date", "sdnn_1"
                ]
                existing = [c for c in cols if c in chunk.columns]
                chunk = chunk[existing]

                for c in existing:
                    chunk[c] = pd.to_numeric(chunk[c], errors="coerce")

                chunk["user"] = user_id
                chunk["device"] = sleep_id

                chunk = chunk.rename(columns={
                    "startdate": "start_date",
                    "enddate": "end_date",
                    "Sleep state": "sleep_state",
                    "Heart Rate date": "date_heart_rate",
                    "Heart Rate": "heart_rate",
                    "Respiration rate date": "date_respiration_rate",
                    "Respiration rate": "respiration_rate",
                    "Snoring date": "date_snoring",
                    "Snoring": "snoring",
                    "sdnn_1 date": "date_sdnn_1",
                    "sdnn_1": "sdnn_1",
                })

                # Cast sleep_state to int when present
                # (do it after NaN->None conversion)
                chunk = nan_to_none_df(chunk)
                records = chunk.to_dict("records")
                for r in records:
                    if r.get("sleep_state") is not None:
                        r["sleep_state"] = int(r["sleep_state"])

                bad = post_rows_bulk_or_threaded(
                    self.session, url, records, use_bulk=use_bulk, max_workers=max_workers
                )
                if bad:
                    print(f"[WARN] {username} intra sleep: {len(bad)} failed rows. First 2: {bad[:2]}")

            print(f"[OK] Intra SleepMat uploaded for {username}")


# =========================
# RUN
# =========================
if __name__ == "__main__":
    path_user = "/home/nathalia/Withings_ScanWatch/Withings_ScanWatch/db/Users.csv"
    db_csv = DatabaseServer_csv(path=path_user, base_url="http://127.0.0.1:8000", pool_maxsize=50)

    db_csv.get_users()

    # Pick what you want to run:
    # db_csv.upload_scanwatch_summary_data(chunksize=5000, use_bulk=True, max_workers=12)
    # db_csv.upload_sleep_summary_data(chunksize=2000, use_bulk=True, max_workers=12)
    # db_csv.upload_intra_scanwatch_summary_data(chunksize=10000, use_bulk=True, max_workers=12)
    db_csv.upload_intra_sleep_summary_data(chunksize=10000, use_bulk=True, max_workers=12)
