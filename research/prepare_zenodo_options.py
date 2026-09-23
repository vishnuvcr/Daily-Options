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


def build_nested_index(archive: Path) -> list[tuple[tuple[str, ...], ContractFile]]:
    def walk(payload: bytes, chain: tuple[str, ...]) -> list[tuple[tuple[str, ...], ContractFile]]:
        rows = []
        with zipfile.ZipFile(io.BytesIO(payload)) as z:
            for member in z.namelist():
                if member.endswith("/"):
                    continue
                next_chain = chain + (member,)
                if member.lower().endswith(".zip"):
                    rows.extend(walk(z.read(member), next_chain))
                    continue
                if not member.lower().endswith((".txt", ".csv", ".xlsx", ".xls")):
                    continue
                virtual_path = Path(*next_chain)
                expiry = parse_expiry_date(virtual_path)
                strike, typ = parse_strike_type(virtual_path)
                if expiry is None or strike is None or typ is None:
                    continue
                rows.append((
                    next_chain,
                    ContractFile(
                        path=member,
                        option_type=typ,
                        strike=float(strike),
                        expiry_date=expiry,
                        expiry_type=expiry_type(expiry),
                    ),
                ))
        return rows

    rows = []
    with zipfile.ZipFile(archive) as outer:
        for member in outer.namelist():
            if member.endswith("/") or not member.lower().endswith(".zip"):
                continue
            rows.extend(walk(outer.read(member), (member,)))
    return rows


def materialize_contract(archive: Path, chain: tuple[str, ...], out: Path) -> Path:
    with zipfile.ZipFile(archive) as outer:
        payload = outer.read(chain[0])
    for member in chain[1:]:
        with zipfile.ZipFile(io.BytesIO(payload)) as z:
            payload = z.read(member)
    target = out.joinpath(*chain)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(payload)
    return target

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
    needed: set[tuple[str, ...]] = set()

    for row in signals.itertuples(index=False):
        for requested in ("WEEK", "MONTH"):
            choices = [
                (chain, cf)
                for chain, cf in index
                if cf.option_type == row.direction
                and cf.expiry_type == requested
                and cf.expiry_date >= row.trade_date
            ]
            if not choices:
                continue
            expiry = min(cf.expiry_date for _, cf in choices)
            for chain, cf in choices:
                if cf.expiry_date == expiry and abs(cf.strike - float(row.spot)) <= 500.0:
                    needed.add(chain)

    args.out.mkdir(parents=True, exist_ok=True)
    for p in sorted(args.out.rglob("*"), reverse=True):
        if p.is_file():
            p.unlink()
        elif p.is_dir():
            p.rmdir()

    for chain in sorted(needed):
        materialize_contract(args.archive, chain, args.out)

    manifest = {
        "archive": str(args.archive),
        "signal_rows": int(len(signals)),
        "indexed_contract_files": int(len(index)),
        "extracted_contract_files": int(len(needed)),
        "available_expiry_types": sorted({cf.expiry_type for _, cf in index}),
        "selected_expiry_types": sorted({cf.expiry_type for chain, cf in index if chain in needed}),
    }
    (args.out.parent / "option_subset_manifest.json").write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
