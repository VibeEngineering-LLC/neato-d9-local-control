"""mitmproxy addon: fake-orbital. Перехватывает запросы к orbital.neatocloud.com, логирует их
(метод/URL/заголовки/тело) и ОТВЕЧАЕТ подделками вместо мёртвого сервера, чтобы приложение прошло
логин и онбординг. Всё остальное mitmdump пропускает через --ignore-hosts. NEATO_MITM_LOG — файл лога."""
from mitmproxy import http
import time, json, os

LOG = os.environ.get("NEATO_MITM_LOG", "mitm_neato_log.txt")
CT = {"Content-Type": "application/vnd.neato.orbital-http.v1+json"}
STUB_FAKE_TOKEN = "FAKE-STUB-neato-local-0123456789"


def _log(s):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(s)


def _fake_payload(method, path):
    if path.endswith("/sessions"):
        return {"token": STUB_FAKE_TOKEN, "access_token": STUB_FAKE_TOKEN, "token_type": "Token"}
    if path.endswith("/users/me/robots"):
        return []
    if path.endswith("/users/me"):
        return {"id": "local-user", "email": "stub-user@example.com", "first_name": "Local",
                "last_name": "User", "country_code": "US", "locale": "en"}
    if path.endswith("/mobile_devices"):
        return {"id": "local-device"}
    if path.endswith("/users") and method == "POST":
        return {"token": STUB_FAKE_TOKEN}
    if "/robots/" in path and path.endswith("/maps"):
        return []
    return {}


def request(flow: http.HTTPFlow):
    host = flow.request.pretty_host.lower()
    if "neatocloud" not in host:
        return
    r = flow.request
    path = r.path.split("?")[0]
    _log("\n=== REQ %s %s %s ===\n" % (time.strftime("%H:%M:%S"), r.method, r.pretty_url))
    _log("".join("H %s: %s\n" % (k, v) for k, v in r.headers.items()))
    body = r.get_text(strict=False) or ""
    if body:
        _log("BODY %s\n" % body[:6000])
    payload = _fake_payload(r.method, path)
    resp_body = json.dumps(payload)
    _log("--> FAKE 200 %s\n" % resp_body[:800])
    flow.response = http.Response.make(200, resp_body.encode("utf-8"), CT)
