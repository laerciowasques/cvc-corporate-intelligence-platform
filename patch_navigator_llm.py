"""Integra LLM hibrido (Vercel + OpenAI) e corrige governanca CEO/CFO atual."""
from pathlib import Path

HTML = Path(__file__).parent / "CVC_Corporate_Intelligence_Platform.html"

OLD_API_BASE = """  apiBase: localStorage.getItem('oracleApiBase') || 'http://127.0.0.1:8000',
  apiReady: false,
  apiChunks: 0,
  chatMessages: [],
};"""

NEW_API_BASE = r"""  apiEndpoints: null,
  apiReady: false,
  apiChunks: 0,
  apiEngine: 'local',
  chatMessages: [],
};

function resolveApiEndpoints() {
  const custom = localStorage.getItem('oracleApiBase');
  if (custom) {
    const base = custom.replace(/\/$/, '');
    return { health: base + '/api/health', chat: base + '/api/chat', mode: 'corporate-oracle', stream: true };
  }
  if (typeof location !== 'undefined' && location.protocol !== 'file:') {
    return { health: '/api/oracle/health', chat: '/api/oracle/chat', mode: 'vercel-llm', stream: true };
  }
  return { health: 'http://127.0.0.1:8000/api/health', chat: 'http://127.0.0.1:8000/api/chat', mode: 'corporate-oracle', stream: true };
}

function apiUrl(path) {
  NavigatorState.apiEndpoints = NavigatorState.apiEndpoints || resolveApiEndpoints();
  if (path.startsWith('http')) return path;
  return location.origin + path;
}"""

OLD_GOV = r"""  if (/ceo/.test(ql) && /2013|2026|histor/.test(ql)) {
    const names = (GH.presidentes || []).map(p => `• ${p.nome} (${p.periodo_label})`).join('<br>');
    return { titulo: 'CEOs identificados (2013–2026)', texto: names, fonte: GH.meta?.fontes?.join('; ') };
  }
  return { titulo: 'Consulta', texto: 'Experimente: "Quem era CFO em 2020?", "Quem era CEO durante a pandemia?", "Conselho em 2018".', fonte: null };
}"""

NEW_GOV = r"""  if (/atual|atualmente|hoje|vigente/.test(ql) || (/quem e|quem eh/.test(ql) && !year)) {
    const today = new Date().toISOString().slice(0, 10);
    const wantCeo = /ceo|presidente/.test(ql) || !/cfo/.test(ql);
    const wantCfo = /cfo/.test(ql);
    const parts = [];
    if (wantCeo) {
      const t = whoAtDate('ceo', today);
      if (t) parts.push(`CEO: ${t.nome} (${t.cargo}) — ${t.periodo_label}.`);
    }
    if (wantCfo) {
      const t = whoAtDate('cfo', today);
      if (t) parts.push(`CFO: ${t.nome} — ${t.periodo_label}.`);
    }
    if (parts.length) {
      return { titulo: 'Executivos atuais', texto: parts.join(' '), fonte: (GH.meta?.fontes || []).join('; ') || 'Governança histórica' };
    }
  }
  if (/ceo/.test(ql) && /2013|2026|histor/.test(ql)) {
    const names = (GH.presidentes || []).map(p => `• ${p.nome} (${p.periodo_label})`).join('<br>');
    return { titulo: 'CEOs identificados (2013–2026)', texto: names, fonte: GH.meta?.fontes?.join('; ') };
  }
  return { titulo: 'Consulta', texto: 'Experimente: "Quem é o CEO atual?", "Quem era CFO em 2020?", "Conselho em 2018".', fonte: null };
}"""

OLD_TRY_GOV = """function tryGovernanceAnswer(query) {
  const ql = normNav(query);
  if (!/(ceo|cfo|presidente|conselho|conselheiro|pandemia)/.test(ql)) return null;"""

NEW_TRY_GOV = """function tryGovernanceAnswer(query) {
  const ql = normNav(query);
  if (!/(ceo|cfo|presidente|conselho|conselheiro|pandemia|atual|executiv|vigente)/.test(ql)) return null;"""

OLD_CHECK = """async function checkOracleHealth() {
  updateOracleStatus('loading', 'Verificando IA GPT-4o (opcional)...');
  try {
    const res = await fetchWithTimeout(NavigatorState.apiBase + '/api/health', { method: 'GET' }, 4000);
    if (!res.ok) throw new Error('HTTP ' + res.status);
    const data = await res.json();
    NavigatorState.apiReady = !!data.index_ready;
    NavigatorState.apiChunks = data.manifest?.total_chunks || 0;
    if (NavigatorState.apiReady) {
      NavigatorState.engine = 'gpt';
      updateOracleStatus('online', 'IA GPT-4o online — respostas enriquecidas disponíveis', NavigatorState.apiChunks);
    } else {
      updateOracleStatus('online', 'Consultor local ativo — base embutida (API sem indexação)', 0);
    }
    return NavigatorState.apiReady;
  } catch (e) {
    NavigatorState.apiReady = false;
    NavigatorState.engine = 'local';
    updateOracleStatus('online', 'Consultor local ativo — base de conhecimento embutida', NavigatorState.corpus?.length || 0);
    return false;
  }
}"""

NEW_CHECK = """async function checkOracleHealth() {
  NavigatorState.apiEndpoints = resolveApiEndpoints();
  updateOracleStatus('loading', 'Verificando IA GPT-4o...');
  const tryList = [NavigatorState.apiEndpoints];
  if (NavigatorState.apiEndpoints.mode === 'vercel-llm') {
    tryList.push({ health: 'http://127.0.0.1:8000/api/health', chat: 'http://127.0.0.1:8000/api/chat', mode: 'corporate-oracle', stream: true });
  }
  for (const ep of tryList) {
    try {
      const res = await fetchWithTimeout(apiUrl(ep.health), { method: 'GET' }, 5000);
      if (!res.ok) continue;
      const data = await res.json();
      if (data.index_ready || data.api_ready) {
        NavigatorState.apiEndpoints = ep;
        NavigatorState.apiReady = true;
        NavigatorState.apiEngine = data.engine || 'gpt-4o';
        NavigatorState.apiChunks = NavigatorState.corpus?.length || data.manifest?.total_chunks || 0;
        NavigatorState.engine = 'gpt';
        const label = ep.mode === 'vercel-llm'
          ? 'IA GPT-4o online — análise profunda (busca local + OpenAI)'
          : 'Corporate Oracle local — GPT-4o RAG completo';
        updateOracleStatus('online', label, NavigatorState.apiChunks);
        return true;
      }
    } catch (_) {}
  }
  NavigatorState.apiReady = false;
  NavigatorState.engine = 'local';
  updateOracleStatus('online', 'Consultor local — adicione OPENAI_API_KEY na Vercel para IA profunda', NavigatorState.corpus?.length || 0);
  return false;
}"""

OLD_FETCH = """    const res = await fetch(NavigatorState.apiBase + '/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Accept': 'text/event-stream' },
      body: JSON.stringify({
        message: q,
        session_id: NavigatorState.sessionId,
        stream: true,
        knowledge_base_ids: ['cvc-ri-portal'],
      }),
    });"""

NEW_FETCH = """    NavigatorState.apiEndpoints = NavigatorState.apiEndpoints || resolveApiEndpoints();
    const ep = NavigatorState.apiEndpoints;
    const searchResult = searchNavigatorCorpus(q, { limit: 14 });
    const evidences = buildEvidenceList(searchResult.hits, []);
    const chatHistory = NavigatorState.chatMessages.filter(m => !m.typing).slice(-8).map(m => ({
      role: m.role === 'user' ? 'user' : 'assistant',
      content: m.text || String(m.html || '').replace(/<[^>]+>/g, ' '),
    }));
    const payload = ep.mode === 'vercel-llm'
      ? { message: q, evidences, history: chatHistory, stream: true }
      : { message: q, session_id: NavigatorState.sessionId, stream: true, knowledge_base_ids: ['cvc-ri-portal'] };
    const res = await fetch(apiUrl(ep.chat), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Accept': 'text/event-stream' },
      body: JSON.stringify(payload),
    });"""

OLD_EXEC = """  if (analysis.domain === 'executivo' || /ceo|cfo|administra|dizia|teleconfer/.test(normNav(query))) {
    extras.executiveMemory = buildExecutiveMemory(query, hits);
  }"""

NEW_EXEC = """  if ((analysis.domain === 'executivo' || /administra|dizia|teleconfer/.test(normNav(query)))
    && !/atual|atualmente|quem e|quem eh/.test(normNav(query))) {
    extras.executiveMemory = buildExecutiveMemory(query, hits);
  }"""

OLD_BTN = """                <button type="button" class="nav-mode-btn nav-mode-gpt active" id="navModeGpt">Consulta Inteligente</button>"""

NEW_BTN = """                <button type="button" class="nav-mode-btn nav-mode-gpt active" id="navModeGpt">IA GPT-4o · Análise Profunda</button>"""

OLD_RUN_CHAT = """  try {
    if (!NavigatorState.corpus) buildNavigatorCorpus();
    if (NavigatorState.engine === 'gpt' && NavigatorState.apiReady) {
      await runOracleQuery(q);
      return;
    }
    const answer = runNavigatorQuery(q, { theme: NavigatorState.theme });"""

NEW_RUN_CHAT = """  try {
    if (!NavigatorState.corpus) buildNavigatorCorpus();
    const quick = tryGovernanceAnswer(q) || tryStructuredAnswer(q);
    if (quick) {
      removeLastChatMessage();
      appendChatMessage('bot', '', formatChatAnswer(quick));
      NavigatorState.history.unshift({ query: q, mode: 'local', engine: 'local', answer: quick, ts: new Date().toISOString() });
      if (NavigatorState.history.length > 30) NavigatorState.history.pop();
      renderNavigatorHistory();
      return;
    }
    if (NavigatorState.engine === 'gpt' && NavigatorState.apiReady) {
      await runOracleQuery(q);
      return;
    }
    const answer = runNavigatorQuery(q, { theme: NavigatorState.theme });"""


def main() -> None:
    html = HTML.read_text(encoding="utf-8")
    for old, new in [
        (OLD_API_BASE, NEW_API_BASE),
        (OLD_GOV, NEW_GOV),
        (OLD_TRY_GOV, NEW_TRY_GOV),
        (OLD_CHECK, NEW_CHECK),
        (OLD_FETCH, NEW_FETCH),
        (OLD_EXEC, NEW_EXEC),
        (OLD_BTN, NEW_BTN),
        (OLD_RUN_CHAT, NEW_RUN_CHAT),
    ]:
        if old not in html:
            raise AssertionError(f"Trecho nao encontrado: {old[:60]}...")
        html = html.replace(old, new, 1)
    HTML.write_text(html, encoding="utf-8")
    print("OK")


if __name__ == "__main__":
    main()
