import base64, json, re
from pathlib import Path

html = Path(__file__).parent.joinpath("CVC_Corporate_Intelligence_Platform.html").read_text(encoding="utf-8")
assert "decodeKbPayload" in html, "loader missing"
m = re.search(r'id="kb-data-b64"[^>]*>([A-Za-z0-9+/=]+)</script>', html)
kb = json.loads(base64.b64decode(m.group(1)))
print("OK indicadores", len(kb["indicadores"]), "releases", len(kb["releases"]))
