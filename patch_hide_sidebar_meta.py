"""Oculta metadados da base no rodape do menu lateral."""
from pathlib import Path

HTML = Path(__file__).parent / "CVC_Corporate_Intelligence_Platform.html"

OLD_CSS = """.sidebar-meta {
  margin-top: 0.45rem;
  font-size: 0.62rem;"""

NEW_CSS = """.sidebar-meta {
  display: none;
  margin-top: 0.45rem;
  font-size: 0.62rem;"""

OLD_FOOTER = """      <footer class="sidebar-footer">
        <p>Powered by <strong>Controladoria CVC</strong></p>
        <p id="sidebarMeta" class="sidebar-meta">Carregando metadados...</p>
      </footer>"""

NEW_FOOTER = """      <footer class="sidebar-footer">
        <p>Powered by <strong>Controladoria CVC</strong></p>
      </footer>"""

OLD_RENDER = """function renderPortableMeta() {
  const el = document.getElementById('sidebarMeta');
  if (!el) return;
  const meta = KB.meta || {};
  const log = PROCESSING_LOG || meta.processing_log || {};
  const resumo = log.resumo || {};
  const gerado = (log.fim || meta.gerado_em || log.consolidado_em || '').slice(0, 10);
  const docs = resumo.documentos_inventariados || meta.total_documentos || '—';
  const idx = resumo.entrada_busca || (KB.search_index || []).length || '—';
  el.innerHTML = [
    `Base consolidada · ${docs} docs · ${idx} índice`,
    gerado ? `Processada em ${gerado}` : '',
    '<span class="portable-badge">Arquivo único · portátil</span>',
  ].filter(Boolean).join('<br>');
}

renderPortableMeta();"""

NEW_RENDER = """function renderPortableMeta() { /* metadados ocultos no menu lateral */ }"""


def main() -> None:
    html = HTML.read_text(encoding="utf-8")
    for old, new in [(OLD_CSS, NEW_CSS), (OLD_FOOTER, NEW_FOOTER), (OLD_RENDER, NEW_RENDER)]:
        if old not in html:
            raise AssertionError(f"Trecho nao encontrado: {old[:50]}...")
        html = html.replace(old, new, 1)
    HTML.write_text(html, encoding="utf-8")
    print("OK")


if __name__ == "__main__":
    main()
