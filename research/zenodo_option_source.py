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
            year = int(m.group(1))
            cal = calendar.monthcalendar(year, month_num)
            thursdays = [w[calendar.THURSDAY] for w in cal if w[calendar.THURSDAY]]
            return date(year, month_num, thursdays[-1])

    # Month-only path with year carried by the outer "NiftyOptions YYYY.zip".
    year_match = re.search(r"(?i)NiftyOptions\s*(20\d{2})", text)
    if year_match:
        for name, month_num in month_names.items():
            if re.search(rf"(?i)\b{re.escape(name)}\b", text):
                year = int(year_match.group(1))
                cal = calendar.monthcalendar(year, month_num)
                thursdays = [w[calendar.THURSDAY] for w in cal if w[calendar.THURSDAY]]
                return date(year, month_num, thursdays[-1])

    return None

def expiry_type(expiry: date) -> str:
    cal = calendar.monthcalendar(expiry.year, expiry.month)
    thursdays = [w[calendar.THURSDAY] for w in cal if w[calendar.THURSDAY]]
    last_thu = date(expiry.year, expiry.month, thursdays[-1])
    return "MONTH" if expiry == last_thu else "WEEK"

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
        try:
            payload = json.loads(index_path.read_text(encoding="utf-8"))
            valid = bool(payload) and all(Path(x["path"]).exists() for x in payload[: min(20, len(payload))])
            if valid:
                return [ContractFile(**{
                    **x,
                    "expiry_date": pd.Timestamp(x["expiry_date"]).date(),
                }) for x in payload]
        except Exception:
            pass
        index_path.unlink(missing_ok=True)

    records: list[ContractFile] = []
    for path in sorted(p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in {".txt", ".csv", ".xlsx", ".xls"}):
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
    suffix = path.suffix.lower()
    if suffix == ".txt":
        df = pd.read_csv(
            path,
            header=None,
            names=["symbol", "trade_date", "trade_time", "open", "high", "low", "close", "volume"],
        )
    elif suffix == ".csv":
        df = pd.read_csv(path)
    else:
        df = pd.read_excel(path)

    cols = {}
    for col in df.columns:
        key = re.sub(r"[^a-z0-9]", "", str(col).strip().lower())
        cols[key] = col

    def pick(*names: str):
        for name in names:
            if name in cols:
                return cols[name]
        return None

    date_col = pick("tradedt", "tradedate", "date", "datetime", "timestamp")
    time_col = pick("tradetime", "time")
    close_col = pick("close", "ltp", "last")

    if date_col is None or close_col is None:
        if suffix == ".csv" and df.shape[1] >= 8:
            df = pd.read_csv(
                path,
                header=None,
                names=["symbol", "trade_date", "trade_time", "open", "high", "low", "close", "volume"],
            )
            date_col, time_col, close_col = "trade_date", "trade_time", "close"
        elif suffix in {".xlsx", ".xls"} and df.shape[1] >= 8:
            df = pd.read_excel(
                path,
                header=None,
                names=["symbol", "trade_date", "trade_time", "open", "high", "low", "close", "volume"],
            )
            date_col, time_col, close_col = "trade_date", "trade_time", "close"
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
    strike, typ = parse_strike_type(path)
    out["option_type"] = typ
    out["strike"] = strike
    out = out.loc[out["datetime_local"].notna() & out["close"].gt(0)].copy()
    out["datetime_local"] = pd.DatetimeIndex(out["datetime_local"])
    out["datetime_utc"] = out["datetime_local"] - pd.Timedelta(hours=5, minutes=30)
    out["trade_date"] = out["datetime_local"].dt.date
    return out

