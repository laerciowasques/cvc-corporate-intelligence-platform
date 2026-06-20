"""Melhora relevancia do chat: respostas diretas, busca por intent, menos ruido."""
from pathlib import Path

HTML = Path(__file__).parent / "CVC_Corporate_Intelligence_Platform.html"

OLD_TRY_GOV_END = """    domain: 'Governança', periodos: [], scanned: NavigatorState.corpus?.length || 0, briefing: null,
  };
}

const NAV_THEMES = ["""

NEW_TRY_GOV_END = """    domain: 'Governança', periodos: [], scanned: NavigatorState.corpus?.length || 0, briefing: null,
  };
}

function makeStructuredAnswer(titulo, resumo, evidencia, domain) {
  const ev = evidencia ? [{
    periodo: evidencia.periodo || '—',
    citacao: extractSentence(String(evidencia.texto || evidencia.tese || evidencia.citacao || ''), 20)[0] || String(evidencia.texto || '').slice(0, 280),
    fonte: evidencia.fonte || evidencia.titulo || 'Base CVC',
    sourceType: evidencia.sourceType || evidencia.tipo || 'Documento',
  }] : [];
  return {
    titulo, resumoExecutivo: resumo, evidencias: ev,
    fontes: ev.map(e => e.fonte).filter(Boolean),
    fontesAgrupadas: ev.length ? { [domain]: ev.map(e => e.fonte) } : {},
    indicadores: [], conclusoes: [], riscos: [], oportunidades: [],
    confidence: { level: 'alto', label: '🟢 Alta' },
    domain, periodos: ev.map(e => e.periodo).filter(p => p && p !== '—'), scanned: NavigatorState.corpus?.length || 0, briefing: null,
  };
}

function detectQueryIntent(q) {
  const ql = normNav(q);
  if (/(ipo|abertura de capital|abriu o capital|abriu capital|companhia aberta|listagem na bolsa|listou na bolsa|bovespa|b3)/.test(ql)) return 'ipo';
  if (/(ticker|cvcb3|codigo na bolsa)/.test(ql)) return 'ticker';
  if (/(que ano|quando|em que ano|em que data)/.test(ql)) return 'temporal';
  if (/(qual foi|quanto|valor de)/.test(ql)) return 'metric';
  return 'general';
}

function tryStructuredAnswer(query) {
  const ql = normNav(query);
  const intent = detectQueryIntent(query);
  buildNavigatorCorpus();
  const corpus = NavigatorState.corpus || [];

  if (intent === 'ipo') {
    const ipoChunk = corpus.find(c => normNav(c.texto).includes('primeiro ano como companhia aberta'))
      || corpus.find(c => /pos[- ]ipo|companhia aberta|abertura de capital/.test(normNav(c.texto)) && !/abertura de \\d+ novas/.test(normNav(c.texto)))
      || (KB.narrativa_evolucao?.capitulos || []).find(c => /ipo|2013/.test(normNav((c.titulo || '') + (c.periodo || ''))));
    const cap = (KB.narrativa_evolucao?.capitulos || []).find(c => normNav(c.periodo || '').includes('2013'));
    const resumo = [
      'A CVC abriu capital (IPO) em 2013, passando a negociar na B3 com o ticker CVCB3.',
      ipoChunk && normNav(ipoChunk.texto || '').includes('primeiro ano como companhia aberta')
        ? 'O release do 4T14/ano 2014 menciona que a CVC completava o primeiro ano como companhia aberta — confirmando a listagem em 2013.'
        : (cap?.tese ? cap.tese : 'A cobertura documental da base inicia em 2013, período pós-IPO de consolidação como companhia aberta.'),
    ].join(' ');
    return makeStructuredAnswer('Abertura de capital (IPO)', resumo, ipoChunk || cap, 'Histórico');
  }

  if (intent === 'ticker') {
    return makeStructuredAnswer('Ticker CVC', 'A CVC Corp negocia na B3 com o ticker CVCB3 (CVC Brasil Operadora e Agência de Viagens S.A.).', null, 'Corporativo');
  }

  if (intent === 'temporal' && /fundacao|fundada|criada|nasceu|origem/.test(ql)) {
    const hit = corpus.find(c => /fundad|criada em|desde 1972|1972/.test(normNav(c.texto)));
    if (hit) return makeStructuredAnswer('Origem da CVC', extractSentence(hit.texto, 30)[0] || hit.texto.slice(0, 300), hit, 'Histórico');
  }

  return null;
}

function expandQueryTokens(query, intent) {
  const extra = [];
  if (intent === 'ipo') extra.push('companhia aberta', 'ipo', 'bovespa', 'cvcb3', 'pos-ipo', 'listagem');
  if (intent === 'temporal') extra.push('ano', 'periodo', 'data');
  return extra;
}

function scoreSentenceForQuery(sentence, query, intent) {
  const sn = normNav(sentence);
  const tokens = tokenizeNav(query);
  let score = tokens.filter(t => sn.includes(t)).length * 4;
  if (intent === 'ipo') {
    if (/companhia aberta|pos[- ]ipo|abertura de capital|bovespa|cvcb3/.test(sn)) score += 25;
    if (/abertura de \\d+ novas|novas lojas|novas franquias/.test(sn)) score -= 20;
  }
  if (intent === 'temporal' && /\\b(19|20)\\d{2}\\b/.test(sentence)) score += 8;
  if (sn.length > 40 && sn.length < 420) score += 3;
  return score;
}

function pickBestEvidence(query, hits, analysis) {
  const intent = detectQueryIntent(query);
  let best = null;
  let bestScore = 0;
  for (const h of hits) {
    const sentences = extractSentence(h.texto, 20);
    const pool = sentences.length ? sentences : [h.texto.slice(0, 320)];
    for (const s of pool) {
      let sc = scoreSentenceForQuery(s, query, intent) + (h.score || 0) * 0.15;
      if (analysis.period && h.periodo && normNav(h.periodo).includes(normNav(analysis.period))) sc += 10;
      if (analysis.year && String(h.periodo || s).includes(String(analysis.year))) sc += 12;
      if (sc > bestScore) { bestScore = sc; best = { sentence: s.trim(), hit: h }; }
    }
  }
  return bestScore >= 4 ? best : null;
}

function synthesizeDirectAnswer(query, hits, analysis) {
  const picked = pickBestEvidence(query, hits, analysis);
  if (!picked) return null;
  const { sentence, hit } = picked;
  const src = `${hit.sourceType || hit.tipo || 'Documento'}${hit.periodo ? ' · ' + hit.periodo : ''}`;
  return `${sentence} (Fonte: ${src})`;
}

const NAV_THEMES = ["""

OLD_DETECT_Q = """function detectQuestionType(q, domain) {
  const ql = normNav(q);
  if (/por que|porque|motivo/.test(ql)) return 'causa';
  if (/o que mudou|mudou|evolui|compar|desde|entre/.test(ql)) return 'mudanca';
  if (/impacto|consequencia|negocio/.test(ql)) return 'impacto';
  if (/como|de que forma/.test(ql)) return 'processo';
  if (domain === 'historico') return 'historico';
  if (/qual foi|quanto/.test(ql)) return 'valor';
  return 'factual';
}"""

NEW_DETECT_Q = """function detectQuestionType(q, domain) {
  const ql = normNav(q);
  if (/por que|porque|motivo/.test(ql)) return 'causa';
  if (/o que mudou|mudou|evolui|compar|desde|entre/.test(ql)) return 'mudanca';
  if (/impacto|consequencia|negocio/.test(ql)) return 'impacto';
  if (/como|de que forma/.test(ql)) return 'processo';
  if (/que ano|quando|em que ano/.test(ql)) return 'temporal';
  if (domain === 'historico') return 'historico';
  if (/qual foi|quanto/.test(ql)) return 'valor';
  return 'factual';
}"""

OLD_SCORE = """function scoreChunk(chunk, analysis, themeTerms) {
  let score = 0;
  const text = normNav(chunk.titulo + ' ' + chunk.texto);
  analysis.tokens.forEach(t => { if (text.includes(t)) score += 3; });"""

NEW_SCORE = """function scoreChunk(chunk, analysis, themeTerms, queryIntent) {
  let score = 0;
  const text = normNav(chunk.titulo + ' ' + chunk.texto);
  analysis.tokens.forEach(t => { if (text.includes(t)) score += 3; });
  if (queryIntent === 'ipo') {
    if (/companhia aberta|pos[- ]ipo|abertura de capital|bovespa|cvcb3|bm.fbo/.test(text)) score += 30;
    if (/abertura de \\d+ novas|novas lojas/.test(text)) score -= 25;
    if (chunk.tipo === 'narrativa' || chunk.tipo === 'release' || chunk.tipo === 'evento') score += 8;
    if (chunk.tipo === 'insight_executivo' && !/companhia aberta|ipo|bovespa/.test(text)) score -= 5;
  }
  if (queryIntent === 'temporal' && analysis.year) {
    if (String(chunk.periodo || '').includes(String(analysis.year))) score += 15;
    else if (chunk.periodo && periodSortKeyNav(chunk.periodo) > periodSortKeyNav('1T' + String(analysis.year).slice(-2))) score -= 8;
  }"""

OLD_SEARCH = """function searchNavigatorCorpus(query, opts = {}) {
  const corpus = buildNavigatorCorpus();
  const analysis = opts.analysis || analyzeQuestion(query);
  const limit = opts.limit || (opts.deep ? 40 : 18);
  const themeTerms = opts.themeTerms || [];

  let candidateIdx = new Set();
  if (NavigatorState.tokenIndex && analysis.tokens.length) {
    analysis.tokens.forEach(t => {
      (NavigatorState.tokenIndex.get(t) || []).forEach(i => candidateIdx.add(i));
    });
  }
  const pool = candidateIdx.size > 5 ? [...candidateIdx].map(i => corpus[i]) : corpus;

  const hits = pool
    .map(c => ({ ...c, score: scoreChunk(c, analysis, themeTerms) }))
    .filter(c => c.score > 0)
    .sort((a, b) => b.score - a.score || periodSortKeyNav(b.periodo) - periodSortKeyNav(a.periodo));

  return { hits: hits.slice(0, limit), analysis, totalScanned: corpus.length };
}"""

NEW_SEARCH = """function searchNavigatorCorpus(query, opts = {}) {
  const corpus = buildNavigatorCorpus();
  const analysis = opts.analysis || analyzeQuestion(query);
  const limit = opts.limit || (opts.deep ? 40 : 18);
  const themeTerms = opts.themeTerms || [];
  const intent = detectQueryIntent(query);
  const extraTerms = expandQueryTokens(query, intent);

  let candidateIdx = new Set();
  const searchTokens = [...new Set([...analysis.tokens, ...extraTerms.map(t => normNav(t).split(/\\s+/)).flat().filter(t => t.length > 2)])];
  if (NavigatorState.tokenIndex && searchTokens.length) {
    searchTokens.forEach(t => {
      (NavigatorState.tokenIndex.get(t) || []).forEach(i => candidateIdx.add(i));
    });
  }
  const pool = candidateIdx.size > 3 ? [...candidateIdx].map(i => corpus[i]) : corpus;

  const hits = pool
    .map(c => ({ ...c, score: scoreChunk(c, analysis, themeTerms, intent) }))
    .filter(c => c.score > 0)
    .sort((a, b) => b.score - a.score || periodSortKeyNav(b.periodo) - periodSortKeyNav(a.periodo));

  return { hits: hits.slice(0, limit), analysis, totalScanned: corpus.length, intent };
}"""

OLD_NARRATIVE_BLOCK = """  if (!parts.length && hits.length) {
    const top = hits[0];
    const sents = extractSentence(top.texto, 50);
    if (analysis.questionType === 'causa') {
      parts.push(`Com base nas evidências: ${sents[0] || top.titulo}`);
      if (sents[1]) parts.push(`Contexto adicional: ${sents[1]}`);
    } else if (analysis.questionType === 'impacto') {
      const impact = hits.find(h => normNav(h.texto).includes('impacto')) || top;
      parts.push(extractSentence(impact.texto, 40)[0] || sents[0] || top.titulo);
    } else if (analysis.questionType === 'mudanca') {
      const cr = crossReference(hits);
      if (cr.length) parts.push(`Foram identificadas mudanças corroboradas em ${cr.length} períodos, com múltiplas fontes por trimestre.`);
      parts.push(sents[0] || top.titulo);
    } else {
      parts.push(sents.slice(0, 2).join('. ') || top.titulo);
    }
  }"""

NEW_NARRATIVE_BLOCK = """  if (!parts.length && hits.length) {
    const direct = synthesizeDirectAnswer(analysis.query, hits, analysis);
    if (direct) {
      parts.push(direct);
    } else {
      const top = hits[0];
      const sents = extractSentence(top.texto, 50);
      if (analysis.questionType === 'causa') {
        parts.push(`Com base nas evidências: ${sents[0] || top.titulo}`);
        if (sents[1]) parts.push(`Contexto adicional: ${sents[1]}`);
      } else if (analysis.questionType === 'impacto') {
        const impact = hits.find(h => normNav(h.texto).includes('impacto')) || top;
        parts.push(extractSentence(impact.texto, 40)[0] || sents[0] || top.titulo);
      } else if (analysis.questionType === 'mudanca') {
        const cr = crossReference(hits);
        if (cr.length) parts.push(`Foram identificadas mudanças corroboradas em ${cr.length} períodos, com múltiplas fontes por trimestre.`);
        parts.push(sents[0] || top.titulo);
      } else {
        parts.push(sents[0] || top.titulo);
      }
    }
  }"""

OLD_RUN_GOV = """  const govAnswer = tryGovernanceAnswer(q);
  if (govAnswer) {
    NavigatorState.history.unshift({ query: q, mode: 'local', engine: 'local', answer: govAnswer, ts: new Date().toISOString() });
    if (NavigatorState.history.length > 30) NavigatorState.history.pop();
    return govAnswer;
  }

  if (options.theme) {"""

NEW_RUN_GOV = """  const govAnswer = tryGovernanceAnswer(q);
  if (govAnswer) {
    NavigatorState.history.unshift({ query: q, mode: 'local', engine: 'local', answer: govAnswer, ts: new Date().toISOString() });
    if (NavigatorState.history.length > 30) NavigatorState.history.pop();
    return govAnswer;
  }

  const structured = tryStructuredAnswer(q);
  if (structured) {
    NavigatorState.history.unshift({ query: q, mode: 'local', engine: 'local', answer: structured, ts: new Date().toISOString() });
    if (NavigatorState.history.length > 30) NavigatorState.history.pop();
    return structured;
  }

  if (options.theme) {"""

OLD_EVIDENCE = """function buildEvidenceList(hits, structuredEvidence) {
  const list = [];
  (structuredEvidence || []).forEach(e => list.push({ ...e, score: 20 }));
  hits.slice(0, optsLimit(hits)).forEach(h => {
    const cite = extractSentence(h.texto, 42)[0] || h.texto.slice(0, 220);
    list.push({
      periodo: h.periodo || '—', tipo: h.tipo, sourceType: h.sourceType,
      citacao: cite, fonte: h.fonte, score: h.score,
    });
  });
  return list.slice(0, 10);
}"""

NEW_EVIDENCE = """function buildEvidenceList(hits, structuredEvidence) {
  const list = [];
  const seen = new Set();
  const add = item => {
    const key = normNav((item.citacao || '').slice(0, 90));
    if (!key || seen.has(key)) return;
    seen.add(key);
    list.push(item);
  };
  (structuredEvidence || []).forEach(e => add({ ...e, score: 20 }));
  hits.slice(0, optsLimit(hits)).forEach(h => {
    const cite = extractSentence(h.texto, 42)[0] || h.texto.slice(0, 220);
    add({
      periodo: h.periodo || '—', tipo: h.tipo, sourceType: h.sourceType,
      citacao: cite, fonte: h.fonte, score: h.score,
    });
  });
  return list.slice(0, 6);
}"""


def main() -> None:
    html = HTML.read_text(encoding="utf-8")
    before = html.count("\n") + 1

    replacements = [
        (OLD_TRY_GOV_END, NEW_TRY_GOV_END),
        (OLD_DETECT_Q, NEW_DETECT_Q),
        (OLD_SCORE, NEW_SCORE),
        (OLD_SEARCH, NEW_SEARCH),
        (OLD_NARRATIVE_BLOCK, NEW_NARRATIVE_BLOCK),
        (OLD_RUN_GOV, NEW_RUN_GOV),
        (OLD_EVIDENCE, NEW_EVIDENCE),
    ]
    for old, new in replacements:
        if old not in html:
            raise AssertionError(f"Trecho não encontrado: {old[:80]}...")
        html = html.replace(old, new, 1)

    assert "tryStructuredAnswer" in html
    assert "synthesizeDirectAnswer" in html
    after = html.count("\n") + 1
    assert abs(after - before) < 150

    HTML.write_text(html, encoding="utf-8")
    print(f"OK — {after} linhas")


if __name__ == "__main__":
    main()
