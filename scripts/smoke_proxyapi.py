#!/usr/bin/env python
"""
smoke_proxyapi — проверка LLM-шлюза ProxyAPI (Этап 2 prep).

1) ключ из окружения (имя переменной — key_env из config/llm.json; значение не выводится);
2) GET /v1/models — модель из конфига присутствует в списке;
3) POST /v1/chat/completions — HTTP 200, непустой content, usage > 0.

Запуск:
    set -a; source <dotenv с PROXYAPI_KEY>; set +a
    python scripts/smoke_proxyapi.py
Выход: 0 — всё ок; 1 — любая проверка провалилась.
"""
import json
import os
import pathlib
import sys
import time
import urllib.error
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")

REPO = pathlib.Path(__file__).resolve().parent.parent
CFG = json.loads((REPO / "config" / "llm.json").read_text(encoding="utf-8"))
BASE = CFG["base_url"].rstrip("/")
MODEL = CFG["model"]
KEY = os.environ.get(CFG["key_env"], "")


def call(method: str, path: str, payload: dict | None = None):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(
        BASE + path,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {KEY}",
            "Content-Type": "application/json",
        },
    )
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8")), time.perf_counter() - t0
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(body)
        except json.JSONDecodeError:
            parsed = {"raw": body[:500]}
        return e.code, parsed, time.perf_counter() - t0


def main() -> None:
    print("=" * 60)
    print(f"Smoke ProxyAPI | base={BASE} | model={MODEL}")
    print("=" * 60)

    # 1. ключ в окружении
    if not KEY:
        print(f"[1] FAIL: {CFG['key_env']} нет в окружении")
        sys.exit(1)
    print(f"[1] OK: ключ {CFG['key_env']} в окружении (len={len(KEY)})")

    # 2. GET /models
    st, data, lat = call("GET", "/models")
    if st != 200:
        print(f"[2] FAIL: GET /models -> HTTP {st}: {data}")
        sys.exit(1)
    ids = [m.get("id", "") for m in data.get("data", [])]
    found = MODEL.lower() in {i.lower() for i in ids}
    print(f"[2] GET /models -> 200, моделей в каталоге: {len(ids)}, latency {lat:.2f}s")
    print(f"    модель {MODEL!r} в списке: {'OK' if found else 'НЕТ'}")
    if not found:
        near = sorted(i for i in ids if "deepseek" in i.lower())[:25]
        print("    доступные deepseek-модели:", *near, sep="\n      ")

    # 3. POST /chat/completions
    # max_tokens: у рассуждающей модели бюджет уходит на reasoning до
    # появления content — 16 токенов кончаются на размышлениях (finish=length).
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": "Ответь одним словом: работает?"}],
        "temperature": 0,
        "max_tokens": 512,
    }
    st, data, lat = call("POST", "/chat/completions", payload)
    print(f"[3] POST /chat/completions -> HTTP {st}, latency {lat:.2f}s")
    if st != 200:
        print(f"    FAIL: {data}")
        sys.exit(1)
    ch = (data.get("choices") or [{}])[0]
    msg = ch.get("message") or {}
    content = msg.get("content") or ""
    usage = data.get("usage") or {}
    print(f"    echo model:  {data.get('model', '')}")
    print(f"    content:    {content!r}")
    print(f"    finish:     {ch.get('finish_reason')}")
    print(f"    usage:      prompt={usage.get('prompt_tokens')} "
          f"completion={usage.get('completion_tokens')} total={usage.get('total_tokens')}")

    ok = found and bool(content) and bool(usage)
    print("=" * 60)
    print("VERDICT:", "OK" if ok else "FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
