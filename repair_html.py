"""Repara HTML corrompido — reconsolida JSON com encoding seguro (base64)."""
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
            fase["knowledge_base"] = "embedded://kb-data"
    data["portable"] = True
    data["consolidado_em"] = datetime.now(timezone.utc).isoformat()
    data["fonte_kb"] = "embedded://kb-data"
    return data


def extract_shell(html: str) -> str:
    """Remove blocos de dados embutidos (incluindo conteúdo corrompido entre tags)."""
    html = re.sub(
        r'<script id="processing-log-data"[^>]*>.*?</script>\s*',
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
    html = re.sub(
        r'<script id="kb-data-b64"[^>]*>.*?</script>\s*',
        "",
        html,
        flags=re.DOTALL,
    )
    # Remove linhas órfãs (texto solto entre aside e script JS)
    html = re.sub(
        r'(</aside>\s*\n\s*</div>\s*\n)\s*(?:[^\n<][^\n]*\n)+(?=\s*<script>\s*\n(?:function decodeKbPayload|const KB))',
        r"\1",
        html,
        flags=re.MULTILINE,
    )
    return html


def embed_data(html: str, kb: dict, log: dict) -> str:
    kb.setdefault("meta", {})["processing_log"] = log
    kb["meta"]["consolidado_em"] = log["consolidado_em"]
    kb["meta"]["portable"] = True

    kb_b64 = base64.b64encode(
        json.dumps(kb, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).decode("ascii")
    log_json = json.dumps(log, ensure_ascii=False, separators=(",", ":"))

    payload = (
        f'<script id="processing-log-data" type="application/json">{log_json}</script>\n'
        f'<script id="kb-data-b64" type="text/plain">{kb_b64}</script>\n'
    )

    marker = "<script>\nfunction decodeKbPayload()"
    if marker not in html:
        marker = "<script>\nconst KB = JSON.parse(decodeKbPayload());"
    if marker not in html:
        raise RuntimeError("Marcador JS const KB não encontrado no HTML.")

    if "function decodeKbPayload()" in html and "decodeKbPayload();" in html:
        html = html.replace(marker, payload + marker, 1)
    else:
        html = html.replace(
            "<script>\nconst KB = JSON.parse(document.getElementById('kb-data').textContent);",
            payload + "<script>\nfunction decodeKbPayload() {\n  const b64 = document.getElementById('kb-data-b64');\n  if (b64 && b64.textContent.trim()) return atob(b64.textContent.trim());\n  throw new Error('Base não encontrada');\n}\nconst KB = JSON.parse(decodeKbPayload());",
            1,
        )
    return html


def patch_kb_loader(html: str) -> str:
    loader = """
function decodeKbPayload() {
  const b64 = document.getElementById('kb-data-b64');
  if (b64 && b64.textContent.trim()) {
    const bin = atob(b64.textContent.trim());
    const bytes = Uint8Array.from(bin, c => c.charCodeAt(0));
    return new TextDecoder('utf-8').decode(bytes);
  }
  const legacy = document.getElementById('kb-data');
  if (legacy) return legacy.textContent;
  throw new Error('Base de conhecimento não encontrada no HTML.');
}
"""
    if "function decodeKbPayload" in html:
        return html
    return html.replace(
        "<script>\nconst KB = JSON.parse(decodeKbPayload());",
        "<script>\n" + loader.strip() + "\nconst KB = JSON.parse(decodeKbPayload());",
        1,
    )


def repair() -> dict:
    kb = json.loads(KB_FILE.read_text(encoding="utf-8"))
    log = sanitize_processing_log(json.loads(LOG_FILE.read_text(encoding="utf-8")))

    html = HTML_FILE.read_text(encoding="utf-8")
    shell = extract_shell(html)
    html = embed_data(shell, kb, log)
    html = patch_kb_loader(html)

    # Garantir meta portátil
    portable_meta = '<meta name="cvc-portable" content="standalone-single-file">'
    if portable_meta not in html:
        html = html.replace("<head>", f"<head>\n{portable_meta}", 1)

    HTML_FILE.write_text(html, encoding="utf-8")

    # Validar
    test_html = HTML_FILE.read_text(encoding="utf-8")
    m = re.search(r'id="kb-data-b64"[^>]*>([A-Za-z0-9+/=]+)</script>', test_html)
    assert m, "kb-data-b64 missing"
    kb_test = json.loads(base64.b64decode(m.group(1)).decode("utf-8"))
    assert len(kb_test.get("indicadores", [])) > 0

    return {
        "html_mb": round(HTML_FILE.stat().st_size / (1024 * 1024), 2),
        "indicadores": len(kb_test.get("indicadores", [])),
        "releases": len(kb_test.get("releases", [])),
        "encoding": "base64",
    }


if __name__ == "__main__":
    info = repair()
    print("Reparo concluído:", info)
