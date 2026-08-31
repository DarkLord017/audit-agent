"""Allowlist vs injected hop-by-hop / Anthropic headers."""

from backend.proxy.routes import ProxyAPI


INJECTED = [
    ("content-type", "application/json"),
    ("x-api-key", "worker-job-token"),
    ("authorization", "Bearer stolen"),
    ("x-forwarded-for", "1.2.3.4"),
    ("x-forwarded-host", "evil.example"),
    ("cookie", "session=x"),
    ("host", "worker"),
    ("anthropic-workspace-id", "attacker-workspace"),
    ("anthropic-dangerous-direct-browser-access", "true"),
    ("anthropic-beta", "prompt-caching-2024-07-31"),
    ("anthropic-version", "2023-06-01"),
]


def test_allowlist_drops_injected_headers(monkeypatch) -> None:
    monkeypatch.setattr(ProxyAPI, "WORKSPACE_ID", "")
    out = ProxyAPI._upstream_headers(INJECTED, "REAL_KEY_NOT_FROM_WORKER")
    keys = {k.lower() for k in out}
    assert "x-forwarded-for" not in keys
    assert "x-forwarded-host" not in keys
    assert "authorization" not in keys
    assert "cookie" not in keys
    assert "host" not in keys
    assert "anthropic-workspace-id" not in keys
    assert "anthropic-dangerous-direct-browser-access" not in keys
    assert out["x-api-key"] == "REAL_KEY_NOT_FROM_WORKER"
    assert out["content-type"] == "application/json"
    assert out["anthropic-beta"] == "prompt-caching-2024-07-31"
    assert out["anthropic-version"] == "2023-06-01"
    assert out["accept-encoding"] == "identity"


def test_workspace_id_comes_from_config_not_worker(monkeypatch) -> None:
    monkeypatch.setattr(ProxyAPI, "WORKSPACE_ID", "from-env")
    out = ProxyAPI._upstream_headers(INJECTED, "REAL_KEY")
    assert out["anthropic-workspace-id"] == "from-env"


def test_default_anthropic_version_when_worker_omits(monkeypatch) -> None:
    monkeypatch.setattr(ProxyAPI, "WORKSPACE_ID", "")
    out = ProxyAPI._upstream_headers(
        [("content-type", "application/json")],
        "REAL_KEY",
    )
    assert out["anthropic-version"] == "2023-06-01"
    assert "anthropic-beta" not in {k.lower() for k in out}
