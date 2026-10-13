from flex import netheal


def test_dead_ip_is_pinned_to_working_frontend(tmp_path, monkeypatch):
    hosts = tmp_path / "hosts"
    hosts.write_text("127.0.0.1 localhost\n1.2.3.4 old.spotify.com # spotify-flex-netheal\n")
    monkeypatch.setattr(netheal, "HOSTS_FILE", hosts)
    monkeypatch.setattr(netheal, "REPORT_FILE", tmp_path / "r.json")
    monkeypatch.setattr(netheal, "_apresolve_hosts", lambda: ["gew4-spclient.spotify.com", "gew1-spclient.spotify.com"])
    dns = {"gew4-spclient.spotify.com": ["35.186.224.28"], "gew1-spclient.spotify.com": ["35.186.224.26"],
           "api.spotify.com": ["35.186.224.24"]}
    monkeypatch.setattr(netheal, "_resolve_v4", lambda h: dns.get(h, []))
    monkeypatch.setattr(netheal, "_tls_ok", lambda ip, host, port=443: ip != "35.186.224.28")
    report = netheal.heal()
    assert report["overrides"] == {"gew4-spclient.spotify.com": "35.186.224.26"}
    text = hosts.read_text()
    assert "35.186.224.26 gew4-spclient.spotify.com" in text
    assert "old.spotify.com" not in text and "localhost" in text


def test_nothing_changes_when_all_reachable(tmp_path, monkeypatch):
    hosts = tmp_path / "hosts"
    hosts.write_text("127.0.0.1 localhost\n")
    monkeypatch.setattr(netheal, "HOSTS_FILE", hosts)
    monkeypatch.setattr(netheal, "REPORT_FILE", tmp_path / "r.json")
    monkeypatch.setattr(netheal, "_apresolve_hosts", lambda: ["gew1-spclient.spotify.com"])
    monkeypatch.setattr(netheal, "_resolve_v4", lambda h: ["35.186.224.26"])
    monkeypatch.setattr(netheal, "_tls_ok", lambda ip, host, port=443: True)
    assert netheal.heal()["overrides"] == {}
    assert hosts.read_text() == "127.0.0.1 localhost\n"
