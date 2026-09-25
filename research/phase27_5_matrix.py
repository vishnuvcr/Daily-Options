#!/usr/bin/env python3
import json,csv
from pathlib import Path

def main():
 root=Path('reports')
 rows=list(csv.DictReader(open(root/'phase27_5_t1_resolution_matrix.csv',encoding='utf-8')))
 assert len(rows)==8
 assert all(r['resolution_state']!='READY_FOR_BACKTEST' for r in rows)
 summary={'t1_candidates':8,'backtest_ready':0,'blocked':8,'external_corroboration_only':True}
 Path(root/'phase27_5_summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
 print(json.dumps(summary,sort_keys=True))

if __name__=='__main__': main()
