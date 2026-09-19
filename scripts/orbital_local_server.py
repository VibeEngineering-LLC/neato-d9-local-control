#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
orbital_local_server.py — самодостаточный локальный сервер-заглушка вместо мёртвого
orbital.neatocloud.com. Клиентская половина vacuula: реализует orbital REST, снятый
перехватом MyNeato 1.5.5 (см. neato/research/myneato-cloud-protocol.md).

Ступень -1 (§33): эталонная реализация payload-логики — neato/scripts/mitm_neato_addon.py
(функция _fake_payload). Здесь она перенесена из mitmproxy-аддона в постоянный HTTP(S)-сервис,
который можно развернуть на Raspberry Pi и на который сможет ходить не только телефон (через
прокси), но и сам робот (через DNS-подмену orbital.neatocloud.com на роутере).

Назначение стенда:
  1) постоянный fake-orbital для приложения (без телефонного прокси, по сети);
  2) ДИАГНОСТИКА барьера робота: если робот через DNS-подмену дойдёт до сервера, в логе
     будет видно, доходит ли он до TLS-handshake и что отвергает (cert-pinning) либо какие
     запросы шлёт. Сейчас реакция робота на РЕАЛЬНО доступный сервер ещё не наблюдалась —
     онбординг обрывался на мёртвом DNS, до сервера робот не доходил.

ЗАПУСК (на малине, Linux):
  # без TLS (локальная проверка curl'ом):
  python3 orbital_local_server.py --http-port 8080
  # с TLS (робот/приложение ходят по https):
  python3 orbital_local_server.py --https-port 8443 --cert cert.pem --key key.pem
  # порт 443 требует прав (setcap 'cap_net_bind_service=+ep' $(which python3)) или redirect.

Переменные окружения:
  NEATO_SRV_LOG      — путь к файлу лога (по умолчанию orbital_local_server.log рядом).
  NEATO_FAKE_ROBOT   — если задан serial, /users/me/robots вернёт одного фейкового робота
                       (для съёма протокола команд); иначе вернёт [].
"""
import argparse
import datetime
import json
import os
import ssl
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

CT_ORBITAL = "application/vnd.neato.orbital-http.v1+json"
STUB_FAKE_TOKEN = "FAKE-STUB-neato-local-0123456789"
LOG_PATH = os.environ.get("NEATO_SRV_LOG",
                          os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                       "orbital_local_server.log"))
FAKE_ROBOT_SERIAL = os.environ.get("NEATO_FAKE_ROBOT", "").strip()
_log_lock = threading.Lock()


def _log(text):
    line = "[%s] %s" % (datetime.datetime.now().isoformat(timespec="seconds"), text)
    with _log_lock:
        with open(LOG_PATH, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    print(line, flush=True)


def _fake_payload(method, path):
    """Ответы, снятые с реального orbital (myneato-cloud-protocol.md). Перенос из
    mitm_neato_addon.py::_fake_payload — единый источник истины по формам ответов."""
    if path.endswith("/sessions"):
        return {"token": STUB_FAKE_TOKEN, "access_token": STUB_FAKE_TOKEN, "token_type": "Token"}
    if path.endswith("/users/me/robots"):
        if FAKE_ROBOT_SERIAL:
            return [{
                "serial": FAKE_ROBOT_SERIAL,
                "vendor": "neato",   # путь /vendors/{vendor}/... — без поля был пустой сегмент
                "prefix": "BotVac",
                "name": "Local D9",
                "model": "vorwerk_vr7",
                "firmware": "1.7.0-2933",
                "timezone": "UTC",
                "secret_key": STUB_FAKE_TOKEN,
                "purchased_at": None,
                "linked_at": "2026-01-01T00:00:00Z",
                "nucleo_url": None,
                "traits": [],
            }]
        return []
    if path.endswith("/users/me"):
        return {"id": "local-user", "email": "stub-user@example.com", "first_name": "Local",
                "last_name": "User", "country_code": "US", "locale": "en"}
    if path.endswith("/mobile_devices"):
        return {"id": "local-device"}
    if path.endswith("/users") and method == "POST":
        return {"token": STUB_FAKE_TOKEN}
    if path.endswith("/app_notifications"):
        return []
    if "spotlight_messages" in path:
        return []
    if "/robots/" in path and path.endswith("/maps"):
        return []
    if "/robots/" in path and path.endswith("/messages"):
        # команда роботу: подтверждаем приём; тело (ability) пишется в лог целиком
        return {"result": "ok", "data": {}}
    return {}


def _message_reply(body):
    """Ответ на POST .../messages. Приложение шлёт {"ability": "<action>", ...}.
    ВАЖНО (реверс APK 19.09): Retrofit+GsonConverterFactory десериализует ТЕЛО ОТВЕТА НАПРЯМУЮ
    в типизированную модель — обёртки {"result","data"} НЕТ. Стаб с обёрткой = все non-null
    Kotlin-поля становятся null → NPE после парсинга. Поэтому отдаём ПЛОСКИЕ объекты-модели
    с реальными полями из декомпиля (пакет retrofit.objects.response). Обязательные (non-null
    String/List) заполнены — без них краш."""
    ability = ""
    try:
        ability = (json.loads(body or b"{}") or {}).get("ability", "")
    except Exception:
        pass
    _log("    ABILITY: %s" % ability)
    if ability == "info.robot":                 # InfoRobotResponse
        return {"serial_number": FAKE_ROBOT_SERIAL or "LOCAL-0000",
                "firmware": "1.7.0-2933"}
    if ability == "info.wifi":                  # InfoWifiResponse
        return {"SSID": "HomeNet", "MAC": "AA:BB:CC:DD:EE:FF", "ip": "192.0.2.30"}
    if ability == "settings.cleaning_options":  # CleaningOptionsResponse
        return {"force_floorplan": False}
    if ability == "settings.robot_language":    # RobotLanguageResponse
        return {"language": "en",
                "available_languages": ["en", "de", "fr", "es", "it", "ru"]}
    if ability == "reminders.get":              # TimerReminderSettingsResponse (пороги int)
        return {"max_threshold": 100, "min_threshold": 0, "threshold": 30}
    if ability == "state.show":                 # StateShowResponse — ГЕЙТ кнопки Play
        # isPlayEnabled: state != null и robotState ∉ {OFFLINE,UNDEFINED};
        # play(): шлёт cleaning.start только при available_commands.start == true.
        # state="idle"+action=""+is_docked=false → IDLE_OFF_BASE (кнопка активна).
        return {
            "state": "idle",
            "action": "",
            "errors": [],
            "available_commands": {"start": True, "stop": False, "pause": False,
                                   "resume": False, "return_to_base": False,
                                   "cancel": False, "extract": False},
            "details": {"base_type": "standard", "charge": "95", "is_charging": False,
                        "is_docked": False, "is_quickboost": False},
            "autonomy_states": {"started_on_base": False},
        }
    if ability == "info.abilities":             # InfoAbilitiesResponse (на Play не влияет)
        return {"cleaning": "1.2.0", "iec_test": None}
    if ability == "cleaning.start":             # EmptyResponse — полей нет
        return {}
    return {}


class Handler(BaseHTTPRequestHandler):
    server_version = "orbital-local/1.0"
    protocol_version = "HTTP/1.1"

    def _handle(self, method):
        path = self.path.split("?")[0]
        length = int(self.headers.get("Content-Length", 0) or 0)
        body = self.rfile.read(length) if length else b""
        hdrs = "".join("    %s: %s\n" % (k, v) for k, v in self.headers.items())
        peer = self.client_address[0] if self.client_address else "?"
        _log("=== REQ %s %s from %s ===\n%s" % (method, self.path, peer, hdrs.rstrip()))
        if body:
            try:
                shown = body.decode("utf-8", "replace")
            except Exception:
                shown = repr(body)
            _log("    BODY: %s" % shown[:6000])
        if method == "POST" and path.endswith("/messages"):
            payload = _message_reply(body)
        else:
            payload = _fake_payload(method, path)
        resp = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", CT_ORBITAL)
        self.send_header("Content-Length", str(len(resp)))
        self.end_headers()
        self.wfile.write(resp)
        _log("    --> 200 %s" % resp.decode("utf-8")[:800])

    def do_GET(self):
        self._handle("GET")

    def do_POST(self):
        self._handle("POST")

    def do_PUT(self):
        self._handle("PUT")

    def do_DELETE(self):
        self._handle("DELETE")

    def log_message(self, fmt, *args):
        pass  # своё логирование через _log


class TLSLoggingHTTPServer(ThreadingHTTPServer):
    """HTTPS-сервер, который ЛОГИРУЕТ сорванный TLS-handshake с адресом клиента.
    Штатный socketserver перехватывает ssl.SSLError (подкласс OSError) в
    _handle_request_noblock и молча возвращается — поэтому обрыв handshake роботом
    из-за cert-pinning не виден ни в логе, ни в journal. Здесь handshake делается в
    get_request() с явным логом ошибки: обрыв на проверке сертификата станет видимым."""

    def __init__(self, addr, handler, ctx):
        self._ctx = ctx
        super().__init__(addr, handler)

    def get_request(self):
        sock, addr = self.socket.accept()
        peer = addr[0] if addr else "?"
        try:
            tls = self._ctx.wrap_socket(sock, server_side=True)
        except (ssl.SSLError, OSError) as exc:
            _log("!!! TLS-HANDSHAKE FAIL from %s: %s" % (peer, exc))
            try:
                sock.close()
            except Exception:
                pass
            raise  # socketserver проглотит OSError штатно; мы уже залогировали
        _log("... TLS-HANDSHAKE OK from %s" % peer)
        return tls, addr


def _serve(server, label):
    _log("LISTEN %s" % label)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


def main():
    ap = argparse.ArgumentParser(description="Локальный orbital.neatocloud.com (заглушка)")
    ap.add_argument("--http-port", type=int, default=0, help="порт plain HTTP (0 = выкл)")
    ap.add_argument("--https-port", type=int, action="append", default=[],
                    help="порт HTTPS; можно указать НЕСКОЛЬКО раз "
                         "(робот Neato ходит на 3443, приложение MyNeato — на 443)")
    ap.add_argument("--bind", default="0.0.0.0", help="адрес прослушки")
    ap.add_argument("--cert", help="путь к TLS-сертификату (PEM)")
    ap.add_argument("--key", help="путь к приватному ключу (PEM)")
    args = ap.parse_args()

    if not args.http_port and not args.https_port:
        args.http_port = 8080  # дефолт для локальной проверки

    _log("START fake-orbital; log=%s; fake_robot=%r" % (LOG_PATH, FAKE_ROBOT_SERIAL or None))
    threads = []

    if args.http_port:
        httpd = ThreadingHTTPServer((args.bind, args.http_port), Handler)
        t = threading.Thread(target=_serve, args=(httpd, "HTTP %s:%d" % (args.bind, args.http_port)),
                             daemon=True)
        t.start()
        threads.append(t)

    if args.https_port:
        if not (args.cert and args.key):
            _log("FATAL: --https-port задан без --cert/--key")
            sys.exit(2)
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.load_cert_chain(certfile=args.cert, keyfile=args.key)
        for hp in args.https_port:  # каждый порт — свой слушающий сервер, общий ctx
            httpsd = TLSLoggingHTTPServer((args.bind, hp), Handler, ctx)
            t = threading.Thread(target=_serve,
                                 args=(httpsd, "HTTPS %s:%d" % (args.bind, hp)),
                                 daemon=True)
            t.start()
            threads.append(t)

    try:
        while True:
            for t in threads:
                t.join(timeout=1.0)
    except KeyboardInterrupt:
        _log("STOP by KeyboardInterrupt")


if __name__ == "__main__":
    main()
