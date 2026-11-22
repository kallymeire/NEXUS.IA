import json, pathlib

def test_metrics_schema():
    m = json.loads(pathlib.Path('docs/dashboard/data/metrics.json').read_text())
    assert {'ml','dbs','ops','trace'} <= m.keys()
