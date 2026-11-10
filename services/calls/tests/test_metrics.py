from types import SimpleNamespace as Seg

from app.metrics import compute_metrics


def test_talk_ratio_and_questions():
    segments = [
        Seg(speaker=0, start_s=0, end_s=10, text="Hello, is this Rahul? I'm calling from Acme."),
        Seg(speaker=1, start_s=10, end_s=15, text="Haan boliye."),
        Seg(speaker=0, start_s=15, end_s=45, text="We have a CRM plan. Would you like a demo?"),
        Seg(speaker=1, start_s=45, end_s=50, text="Price kya hai?"),
    ]
    m = compute_metrics(segments, rep_speaker=0)
    assert m["rep_talk_s"] == 40
    assert m["customer_talk_s"] == 10
    assert m["rep_talk_ratio"] == 0.8
    assert m["longest_rep_monologue_s"] == 30
    assert m["rep_questions"] == 2
    assert m["customer_questions"] == 1
    assert m["turns"] == 4


def test_empty_call():
    assert compute_metrics([], rep_speaker=0)["rep_talk_ratio"] == 0.0
