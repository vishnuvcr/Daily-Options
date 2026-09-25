import csv
from research.phase27_5_matrix import main

def test_matrix_has_eight_candidates():
 rows=list(csv.DictReader(open('reports/phase27_5_t1_resolution_matrix.csv',encoding='utf-8')))
 assert len(rows)==8
 assert all(r['resolution_state'] != 'READY_FOR_BACKTEST' for r in rows)
