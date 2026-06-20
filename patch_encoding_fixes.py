"""Corrige mojibake (UTF-8 via atob) e labels camelCase na Central de Resultados."""
from pathlib import Path

HTML = Path(__file__).parent / "CVC_Corporate_Intelligence_Platform.html"

OLD_DECODE = """function decodeKbPayload() {
  const b64 = document.getElementById('kb-data-b64');
  if (b64 && b64.textContent.trim()) {
    return atob(b64.textContent.trim());
  }
  const legacy = document.getElementById('kb-data');
  if (legacy) return legacy.textContent;
  throw new Error('Base de conhecimento não encontrada no HTML.');
}"""

NEW_DECODE = """function decodeKbPayload() {
  const b64 = document.getElementById('kb-data-b64');
  if (b64 && b64.textContent.trim()) {
    const bin = atob(b64.textContent.trim());
    const bytes = Uint8Array.from(bin, c => c.charCodeAt(0));
    return new TextDecoder('utf-8').decode(bytes);
  }
  const legacy = document.getElementById('kb-data');
  if (legacy) return legacy.textContent;
  throw new Error('Base de conhecimento não encontrada no HTML.');
}"""

OLD_IND = "const ind = r.indicadores ? Object.entries(r.indicadores).map(([k,v]) => `<span class=\"tag\">${k}: ${v}</span>`).join(' ') : '';"
NEW_IND = """const ind = r.indicadores ? Object.entries(r.indicadores).map(([k,v]) => {
        const lbl = RESULT_METRIC_LABELS[k] || k.replace(/([A-Z])/g, ' $1').replace(/_/g, ' ').replace(/^\\s+|\\b\\w/g, s => s.toUpperCase()).trim();
        return `<span class="tag">${escHtml(lbl)}: ${v}</span>`;
      }).join(' ') : '';"""

METRIC_LABELS_BLOCK = """const RESULT_METRIC_LABELS = {
  receitaLiquida: 'Receita Líquida', receita_liquida: 'Receita Líquida',
  reservasConfirmadas: 'Reservas Confirmadas', reservas_confirmadas: 'Reservas Confirmadas',
  reservasConsumidas: 'Reservas Consumidas', reservas_consumidas: 'Reservas Consumidas',
  takeRate: 'Take Rate', take_rate: 'Take Rate',
  lucroLiquido: 'Lucro Líquido', lucro_liquido: 'Lucro Líquido',
  ebitdaAjustado: 'EBITDA Ajustado', ebitda_ajustado: 'EBITDA Ajustado',
  dividaLiquida: 'Dívida Líquida', divida_liquida: 'Dívida Líquida',
  alavancagem: 'Alavancagem', caixa: 'Caixa', margemEbitda: 'Margem EBITDA', margem_ebitda: 'Margem EBITDA',
};

"""


def main() -> None:
    html = HTML.read_text(encoding="utf-8")
    before_lines = html.count("\n") + 1
    assert "decodeKbPayload" in html, "HTML base inválido"
    assert OLD_DECODE in html, "decodeKbPayload original não encontrado"
    assert OLD_IND in html, "renderResults indicadores não encontrado"
    assert "RESULT_METRIC_LABELS" not in html, "Patch já aplicado?"

    html = html.replace(OLD_DECODE, NEW_DECODE, 1)
    html = html.replace(
        "function renderResults() {",
        METRIC_LABELS_BLOCK + "function renderResults() {",
        1,
    )
    html = html.replace(OLD_IND, NEW_IND, 1)

    assert "TextDecoder" in html
    assert "RESULT_METRIC_LABELS" in html
    assert OLD_DECODE not in html
    after_lines = html.count("\n") + 1
    assert abs(after_lines - before_lines) < 30, f"Linhas mudaram demais: {before_lines} -> {after_lines}"

    HTML.write_text(html, encoding="utf-8")
    print(f"OK — {after_lines} linhas, {HTML.stat().st_size / (1024 * 1024):.2f} MB")


if __name__ == "__main__":
    main()
