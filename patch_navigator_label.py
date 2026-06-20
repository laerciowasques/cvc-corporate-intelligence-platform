"""Patch seguro no HTML grande — remove pulse e adiciona label em desenvolvimento."""
from pathlib import Path

HTML = Path(__file__).parent / "CVC_Corporate_Intelligence_Platform.html"

OLD_CSS = """@keyframes navPulse {
  0%, 100% {
    color: var(--accent);
    border-left-color: var(--accent);
    background: rgba(0,212,170,0.05);
  }
  33% {
    color: var(--text);
    border-left-color: var(--text);
    background: rgba(255,255,255,0.04);
  }
  66% {
    color: var(--muted);
    border-left-color: var(--muted);
    background: rgba(139,156,179,0.06);
  }
}
.nav-item--pulse {
  animation: navPulse 3s ease-in-out infinite;
  font-weight: 500;
  border-left-color: var(--accent);
}
.nav-item--pulse:hover {
  animation-play-state: paused;
  color: var(--text);
  background: rgba(0,212,170,0.1);
  border-left-color: var(--accent);
}
.nav-item--pulse.active {
  animation: none;
  color: var(--text);
  background: rgba(0,212,170,0.06);
  border-left-color: var(--accent);
}"""

NEW_CSS = """.nav-dev-label {
  display: block;
  margin-top: 0.2rem;
  font-size: 0.68rem;
  font-weight: 600;
  color: var(--warn);
  letter-spacing: 0.03em;
  line-height: 1.3;
}"""

OLD_NAV = '<a class="nav-item nav-item--pulse" data-panel="navigator">CVC Navigator</a>'
NEW_NAV = '<a class="nav-item" data-panel="navigator">CVC Navigator<span class="nav-dev-label">(em desenvolvimento)</span></a>'


def main() -> None:
    html = HTML.read_text(encoding="utf-8")
    before_lines = html.count("\n") + 1
    assert "decodeKbPayload" in html, "HTML base inválido"
    assert OLD_CSS in html, "CSS pulse não encontrado"
    assert OLD_NAV in html, "Nav item pulse não encontrado"

    html = html.replace(OLD_CSS, NEW_CSS, 1)
    html = html.replace(OLD_NAV, NEW_NAV, 1)

    assert "nav-dev-label" in html
    assert "nav-item--pulse" not in html
    assert "decodeKbPayload" in html
    after_lines = html.count("\n") + 1
    assert abs(after_lines - before_lines) < 50, f"Linhas mudaram demais: {before_lines} -> {after_lines}"

    HTML.write_text(html, encoding="utf-8")
    print(f"OK — {after_lines} linhas, {HTML.stat().st_size / (1024*1024):.2f} MB")


if __name__ == "__main__":
    main()
