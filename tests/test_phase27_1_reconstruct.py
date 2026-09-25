from research.phase27_1_reconstruct import build, status

def test_status_conflict():
    assert status([{"value":"Wednesday","start_sec":1},{"value":"Thursday","start_sec":2}])=="CONFLICTING"

def test_build_timestamped_context():
    seg=[
      {"start":0,"text":"Enter on Wednesday at 9:20 and sell one call."},
      {"start":10,"text":"Adjust on Thursday and close on Monday. Stop at 50%."},
    ]
    r=build("x","Iron Fly","",seg)
    assert r["fields"]["entry_day"][0]["value"].lower()=="wednesday"
    assert r["fields"]["entry_action"]
    assert r["field_status"]["entry_day"]=="SOURCE-EXPLICIT"
