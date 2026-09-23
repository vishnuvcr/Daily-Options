from __future__ import annotations

import argparse
import io
import json
import zipfile
from pathlib import Path

import pandas as pd

from research.zenodo_option_source import ContractFile, parse_expiry_date, parse_strike_type, expiry_type
from research.phase3i_option_execution import build_signal_events
from research.phase3i_futures_spot_lead_lag import identify_spot_futures


def build_nested_index(archive: Path) -> list[tuple[str, str, ContractFile]]:
    rows = []
    with zipfile.ZipFile(archive) as outer:
        nested_members = [x for x in outer.namelist() if x.lower().endswith(".zip")]
        print("INNER_ARCHIVE_COUNT", len(nested_members))
        for outer_member in nested_members:
            raw = outer.read(outer_member)
            with zipfile.ZipFile(io.BytesIO(raw)) as inner:
                members = [m for m in inner.namelist() if not m.endswith("/")]
                print("INNER_ARCHIVE", outer_member, "FILE_COUNT", len(members))
                if members:
                    print("INNER_ARCHIVE_SAMPLE", members[:40])
                for month_member in members[:3]:
                    if month_member.lower().endswith(".zip"):
                        try:
                            month_raw = inner.read(month_member)
                            with zipfile.ZipFile(io.BytesIO(month_raw)) as month_zip:
                                month_files = [m for m in month_zip.namelist() if not m.endswith("/")]
                                print("MONTH_ARCHIVE", month_member, "FILE_COUNT", len(month_files))
                                print("MONTH_ARCHIVE_SAMPLE", month_files[:60])
                                for mf in month_files[:5]:
                                    if mf.lower().endswith(".txt") or mf.lower().endswith(".csv"):
                                        raw = month_zip.read(mf)
                                        print("CONTRACT_SAMPLE", outer_member, month_member, mf)
                                        print(raw[:1200].decode("utf-8", errors="replace"))
                                # One deeper CSV/TXT archive sample for later years.
                                for mf in month_files[:5]:
                                    if mf.lower().endswith(".zip"):
                                        nested_raw = month_zip.read(mf)
                                        with zipfile.ZipFile(io.BytesIO(nested_raw)) as nested_zip:
                                            nested_files = [m for m in nested_zip.namelist() if not m.endswith("/")][:5]
                                            print("DEEP_ARCHIVE", mf, "FILES", nested_files)
                                            for df in nested_files[:2]:
                                                raw = nested_zip.read(df)
                                                print("DEEP_CONTRACT_SAMPLE", mf, df)
                                                print(raw[:1200].decode("utf-8", errors="replace"))
                        except Exception as exc:
                            print("MONTH_ARCHIVE_ERROR", month_member, repr(exc))
                for member in members:
                    lower = member.lower()
                    if not lower.endswith((".csv", ".xlsx", ".xls")):
                        continue
                    p = Path(member)
                    expiry = parse_expiry_date(p)
                    strike, typ = parse_strike_type(p)
                    if expiry is None or strike is None or typ is None:
                        continue
                    rows.append(
                        (
                            outer_member,
                            member,
                            ContractFile(
                                path=str(member),
                                option_type=typ,
                                strike=float(strike),
                                expiry_date=expiry,
                                expiry_type=expiry_type(expiry),
                            ),
                        )
                    )
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--archive", type=Path, required=True)
    ap.add_argument("--futures", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    spot, fut, _ = identify_spot_futures(args.futures)
    signals = build_signal_events(spot, fut)
    signals["trade_date"] = pd.to_datetime(signals["trade_date"]).dt.date
    signals["spot"] = pd.to_numeric(signals["spot"], errors="coerce")

    index = build_nested_index(args.archive)
    needed: dict[str, set[str]] = {}

    for row in signals.itertuples(index=False):
        for et in ("WEEK", "MONTH"):
            choices = [
                (outer, member, cf)
                for outer, member, cf in index
                if cf.option_type == row.direction
                and cf.expiry_type == et
                and cf.expiry_date >= row.trade_date
            ]
            if not choices:
                continue
            expiry = min(cf.expiry_date for _, _, cf in choices)
            around = [
                (outer, member, cf)
                for outer, member, cf in choices
                if cf.expiry_date == expiry and abs(cf.strike - float(row.spot)) <= 500.0
            ]
            for outer, member, _ in around:
                needed.setdefault(outer, set()).add(member)

    args.out.mkdir(parents=True, exist_ok=True)
    for p in args.out.rglob("*"):
        if p.is_file():
            p.unlink()

    extracted = 0
    for outer_member, members in needed.items():
        with zipfile.ZipFile(args.archive) as outer:
            raw = outer.read(outer_member)
        with zipfile.ZipFile(io.BytesIO(raw)) as inner:
            for member in sorted(members):
                target = args.out / Path(member)
                target.parent.mkdir(parents=True, exist_ok=True)
                with inner.open(member) as src, target.open("wb") as dst:
                    dst.write(src.read())
                extracted += 1

    manifest = {
        "archive": str(args.archive),
        "signal_rows": int(len(signals)),
        "nested_year_archives": len(needed),
        "indexed_contract_files": len(index),
        "extracted_contract_files": extracted,
        "expiry_types_requested": ["WEEK", "MONTH"],
    }
    (args.out.parent / "option_subset_manifest.json").write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
