# Strategy Error Log — OTM1 / 2xOTM2 Ratio Backspread

No errors yet.

Any implementation, data-integrity, execution, or workflow defect found in this branch will be logged with identifier, date, phase, impact, corrective action and resolution status.


| EOTM12-001 | 2026-09-29 | Phase A workflow validation | GitHub expression placeholders for matrix friction were escaped into the committed YAML, which could pass a literal value instead of 0.20/0.40 | Current P&L run is non-evidentiary until corrected | Rewrote workflow expressions as native [object Object] expressions; branch push triggers corrected run | CLOSED — pre-P&L |

| EOTM12-002 | 2026-09-29 | Phase A data acquisition | The workflow did not install huggingface_hub, so the pinned dataset acquisition step failed with ModuleNotFoundError | No P&L accepted; Base/Stress acquisition blocked | Added huggingface_hub to workflow dependencies; corrected branch push triggers a new run | CLOSED — pre-P&L |

| EOTM12-003 | 2026-09-29 | Phase A engine | DuckDB 1.5 rejected direct CAST(TIMESTAMP WITH TIME ZONE AS TIME) in the NIFTY query | No P&L accepted | Set DuckDB session timezone to Asia/Kolkata and cast through TIMESTAMP before TIME comparisons in index/option queries | CLOSED — pre-P&L |
