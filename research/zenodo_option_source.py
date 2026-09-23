from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date, datetime
import calendar
from pathlib import Path

import pandas as pd


DATE_PATTERNS = (
    "%d-%b-%Y",
    "%d-%b-%y",
    "%d%b%Y",
    "%d_%b_%Y",
    "%d-%m-%Y",
    "%Y-%m-%d",
    "%Y%m%d",
)


@dataclass(frozen=True)
class ContractFile:
    path: str
    option_type: str
    strike: float
    expiry_date: date
    expiry_type: str


def parse_expiry_date(path: Path) -> date | None:
    text = " / ".join(path.parts)

    # Prefer explicit expiry-day/range dates embedded in archive names.
    explicit: list[date] = []
    for m in re.finditer(r"(?<!\d)(\d{1,2})[-/]([A-Za-z]{3}|\d{1,2})[-/](\d{2,4})(?!\d)", text):
        raw = m.group(0)
        for fmt in ("%d-%m-%Y", "%d-%m-%y", "%d/%m/%Y", "%d/%m/%y", "%d-%b-%Y", "%d-%b-%y"):
            try:
                explicit.append(datetime.strptime(raw, fmt).date())
                break
            except ValueError:
                pass
    if explicit:
        return max(explicit)

    month_names = {m.lower(): i for i, m in enumerate(calendar.month_name) if m}
    month_names.update({m.lower(): i for i, m in enumerate(calendar.month_abbr) if m})

    # Month + year path, e.g. "December 2017.zip".
    for name, month_num in month_names.items():
        m = re.search(rf"(?i)\b{re.escape(name)}[\s_-]*(20\d{{2}})\b", text)
        if m:
            return date(int(m.group(1)), month_num, 1)  # converted to expiry below

    # Month-only path with year carried by the outer "NiftyOptions YYYY.zip".
    year_match = re.search(r"(?i)NiftyOptions\s*(20\d{2})", text)
    if year_match:
        for name, month_num in month_names.items():
            if re.search(rf"(?i)\b{re.escape(name)}\b", text):
                return date(int(year_match.group(1)), month_num, 1)

    return None

def expiry_type(expiry: date) -> str:
    # Files without an explicit expiry-day are represented by the
    # expiry month; classify its last Thursday as the monthly contract.
    cal = calendar.monthcalendar(expiry.year, expiry.month)
    thursdays = [w[calendar.THURSDAY] for w in cal if w[calendar.THURSDAY]]
    last_thu = date(expiry.year, expiry.month, thursdays[-1])
    return "MONTH" if expiry.day == 1 or expiry == last_thu else "WEEK"

def parse_strike_type(path: Path) -> tuple[float | None, str | None]:
    name = path.name.upper().strip()
    m = re.search(r"^\s*(CE|PE)\s*([0-9]{3,6}(?:\.[0-9]+)?)", name)
    if m:
        return float(m.group(2)), ("CALL" if m.group(1) == "CE" else "PUT")

    m = re.search(r"(?:NIFTY\s*)?([0-9]{3,6}(?:\.[0-9]+)?)\s*(CE|PE)", name)
    if m:
        return float(m.group(1)), ("CALL" if m.group(2) == "CE" else "PUT")
    return None, None

def discover_option_files(root: Path, index_path: Path | None = None) -> list[ContractFile]:
    if index_path and index_path.exists():
        payload = json.loads(index_path.read_text(encoding="utf-8"))
        return [ContractFile(**{
            **x,
            "expiry_date": pd.Timestamp(x["expiry_date"]).date(),
        }) for x in payload]

    records: list[ContractFile] = []
    for path in sorted(p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in {".csv", ".xlsx", ".xls"}):
        expiry = parse_expiry_date(path)
        strike, typ = parse_strike_type(path)
        if expiry is None or strike is None or typ is None:
            continue
        records.append(
            ContractFile(
                path=str(path),
                option_type=typ,
                strike=float(strike),
                expiry_date=expiry,
                expiry_type=expiry_type(expiry),
            )
        )

    if index_path is not None:
        index_path.parent.mkdir(parents=True, exist_ok=True)
        index_path.write_text(
            json.dumps(
                [
                    {**x.__dict__, "expiry_date": x.expiry_date.isoformat()}
                    for x in records
                ],
                indent=2,
            ),
            encoding="utf-8",
        )
    return records


def read_contract_file(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".csv":
        df = pd.read_csv(path)
        if df.shape[1] < 5:
            df = pd.read_csv(path, header=None)
    else:
        df = pd.read_excel(path)

    cols = {}
    for c in df.columns:
        key = re.sub(r"[^a-z0-9]", "", str(c).strip().lower())
        cols[key] = c

    def pick(*names: str):
        for n in names:
            if n in cols:
                return cols[n]
        return None

    date_col = pick("tradedt", "tradedate", "date", "datetime", "timestamp")
    time_col = pick("tradetime", "time")
    close_col = pick("close", "ltp", "last")
    type_col = pick("opttype", "optiontype", "type")
    strike_col = pick("strikeprice", "strike")
    if date_col is None or close_col is None:
        # Retry common headerless format used by this dataset.
        if df.shape[1] >= 9:
            df = pd.read_csv(path, header=None) if path.suffix.lower() == ".csv" else pd.read_excel(path, header=None)
            df.columns = [
                "option_type", "strike_price", "trade_date", "trade_time",
                "open", "high", "low", "close", "volume",
            ][: len(df.columns)]
            date_col, time_col, close_col = "trade_date", "trade_time", "close"
            type_col, strike_col = "option_type", "strike_price"
        else:
            raise ValueError(f"Unrecognized option schema: {path.name} / {list(df.columns)}")

    if time_col is None:
        dt = pd.to_datetime(df[date_col], errors="coerce")
    else:
        dt = pd.to_datetime(
            df[date_col].astype(str).str.strip() + " " + df[time_col].astype(str).str.strip(),
            errors="coerce",
        )

    out = pd.DataFrame({
        "datetime_local": dt,
        "close": pd.to_numeric(df[close_col], errors="coerce"),
    })
    if type_col is not None:
        out["option_type"] = df[type_col].astype(str).str.upper().map({"CE": "CALL", "PE": "PUT"}).fillna(df[type_col].astype(str).str.upper())
    if strike_col is not None:
        out["strike"] = pd.to_numeric(df[strike_col], errors="coerce")
    out = out.loc[out["datetime_local"].notna() & out["close"].gt(0)].copy()
    out["datetime_local"] = pd.DatetimeIndex(out["datetime_local"])
    out["datetime_utc"] = out["datetime_local"] - pd.Timedelta(hours=5, minutes=30)
    out["trade_date"] = out["datetime_local"].dt.date
    return out
