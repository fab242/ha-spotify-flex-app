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


def test_access_points_are_never_pinned(tmp_path, monkeypatch):
    import io, json
    hosts = tmp_path / "hosts"
    hosts.write_text("")
    monkeypatch.setattr(netheal, "HOSTS_FILE", hosts)
    monkeypatch.setattr(netheal, "REPORT_FILE", tmp_path / "r.json")
    payload = {"spclient": ["gew4-spclient.spotify.com:443"], "dealer": ["gew4-dealer.spotify.com:443"],
               "accesspoint": ["ap-gew4.spotify.com:443"]}

    class Resp(io.BytesIO):
        def __enter__(self): return self
        def __exit__(self, *a): return False

    monkeypatch.setattr(netheal.urllib.request, "urlopen", lambda url, timeout=0: Resp(json.dumps(payload).encode()))
    found = netheal._apresolve_hosts()
    assert found == ["gew4-spclient.spotify.com", "gew4-dealer.spotify.com"]
