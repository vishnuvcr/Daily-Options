from pathlib import Path
import importlib.util
p=Path("research/phase30_13_low_vix_diagonal_resolution.py")
s=importlib.util.spec_from_file_location("m",p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m)
def test_video_id(): assert m.VIDEO_ID=="6_W4UpFsehs"
def test_ts_seconds(): assert abs(m.ts_seconds("01:02:03.500")-3723.5)<1e-9
def test_clean_vtt():
    x="WEBVTT\n\n00:00:01.000 --> 00:00:02.000\n<00:01>Low VIX\n"
    assert m.clean_vtt(x)=="Low VIX"
