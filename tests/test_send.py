import json

from sitekick import send


def fake_get_domain_info(domain):
    return {"domain": domain}


def test_every_domain_is_queued(tmp_path):
    domains = [f"site{i}.example.com" for i in range(120)]
    send.get_domains_info(domains, fake_get_domain_info, queue_path=tmp_path, show_progress=False)
    files = sorted(tmp_path.glob("*.json"))
    assert len(files) == len(domains)
    record = json.loads(files[0].read_text())
    assert record["meta"]["domain"] == "site0.example.com"


def test_duplicate_domains_are_queued_once(tmp_path):
    domains = ["Example.com", "example.com ", "example.org"]
    send.get_domains_info(domains, fake_get_domain_info, queue_path=tmp_path, show_progress=False)
    assert len(list(tmp_path.glob("*.json"))) == 2
