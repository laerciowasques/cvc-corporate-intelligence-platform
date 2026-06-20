#!/usr/bin/env python3
"""
Consolida knowledge_base.json e processing_log.json no HTML portátil (base64).
Uso: python consolidate_platform.py
"""

from __future__ import annotations

import base64
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HTML_FILE = ROOT / "CVC_Corporate_Intelligence_Platform.html"
KB_FILE = ROOT / "knowledge_base.json"
LOG_FILE = ROOT / "processing_log.json"


def sanitize_processing_log(log: dict) -> dict:
    data = json.loads(json.dumps(log, ensure_ascii=False))
    for fase in data.get("fases_executadas", []):
        if "knowledge_base" in fase:
            fase["knowledge_base"] = "embedded://kb-data-b64"
    data["portable"] = True
    data["consolidado_em"] = datetime.now(timezone.utc).isoformat()
    data["fonte_kb"] = "embedded://kb-data-b64"
    return data


def extract_shell(html: str) -> str:
    html = re.sub(
        r'<script id="processing-log-data"[^>]*>.*?</script>\s*',
        "",
        html,
        flags=re.DOTALL,
    )
    html = re.sub(
        r'<script id="kb-data-b64"[^>]*>.*?</script>\s*',
        "",
        html,
        flags=re.DOTALL,
    )
    html = re.sub(
        r'<script id="kb-data"[^>]*>.*?</script>\s*',
        "",
        html,
        flags=re.DOTALL,
    )
    return html


def consolidate() -> dict:
    if not all(p.exists() for p in (HTML_FILE, KB_FILE, LOG_FILE)):
        raise FileNotFoundError("HTML, knowledge_base.json ou processing_log.json ausente.")

    kb = json.loads(KB_FILE.read_text(encoding="utf-8"))
    log = sanitize_processing_log(json.loads(LOG_FILE.read_text(encoding="utf-8")))
    kb.setdefault("meta", {})["processing_log"] = log
    kb["meta"]["consolidado_em"] = log["consolidado_em"]
    kb["meta"]["portable"] = True

    kb_b64 = base64.b64encode(
        json.dumps(kb, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).decode("ascii")
    log_json = json.dumps(log, ensure_ascii=False, separators=(",", ":"))

    html = extract_shell(HTML_FILE.read_text(encoding="utf-8"))

    payload = (
        f'<script id="processing-log-data" type="application/json">{log_json}</script>\n'
        f'<script id="kb-data-b64" type="text/plain">{kb_b64}</script>\n'
    )

    marker = "<script>\nfunction decodeKbPayload()"
    if marker not in html:
        raise RuntimeError("HTML sem decodeKbPayload() — execute repair_html.py primeiro.")

    html = html.replace(marker, payload + marker, 1)

    portable_meta = '<meta name="cvc-portable" content="standalone-single-file">'
    if portable_meta not in html:
        html = html.replace("<head>", f"<head>\n{portable_meta}", 1)

    HTML_FILE.write_text(html, encoding="utf-8")

    return {
        "output": str(HTML_FILE),
        "html_mb": round(HTML_FILE.stat().st_size / (1024 * 1024), 2),
        "indicadores": len(kb.get("indicadores", [])),
        "encoding": "base64",
    }


if __name__ == "__main__":
    info = consolidate()
    print("Consolidação concluída:")
    for k, v in info.items():
        print(f"  {k}: {v}")
