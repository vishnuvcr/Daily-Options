from pathlib import Path
import importlib.util
spec=importlib.util.spec_from_file_location('p25',Path('research/phase25_falcon_rissin.py'))
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
def test_grid_is_frozen(): assert len(m.variant_grid())==270
def test_offsets(): assert m.expiry_offsets()==(-4,-3,-1)
def test_lot_sizes():
 assert m.lot_size('2024-04-25')==50
 assert m.lot_size('2024-11-21')==75
 assert m.lot_size('2026-01-06')==65
def test_pin(): assert m.RISSIN_REVISION.startswith('78b1c546')
