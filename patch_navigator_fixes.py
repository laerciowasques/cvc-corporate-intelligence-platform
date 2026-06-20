"""Corrige Navigator: fallback local, remove modos extras, limpa histórico no refresh."""
from pathlib import Path

HTML = Path(__file__).parent / "CVC_Corporate_Intelligence_Platform.html"

OLD_BUTTONS = """                <button type="button" class="nav-mode-btn nav-mode-gpt active" id="navModeGpt">IA GPT-4o</button>
                <button type="button" class="nav-mode-btn" id="navModeDeep">Análise Profunda</button>
                <button type="button" class="nav-mode-btn" id="navModeInvestigate">Investigar Tema</button>
                <button type="button" class="nav-mode-btn" id="navModeBriefing">Gerar Executive Briefing</button>
                <button type="button" class="nav-mode-btn" id="navModeDiscover">Descobrir Insights</button>"""

NEW_BUTTONS = """                <button type="button" class="nav-mode-btn nav-mode-gpt active" id="navModeGpt">Consulta Inteligente</button>"""

OLD_STATUS = "<span>Verificando IA GPT-4o...</span>"

NEW_STATUS = "<span>Inicializando consultor...</span>"

OLD_STATE = """const NavigatorState = {
  history: [],
  mode: 'normal',
  engine: 'gpt',
  theme: null,
  corpus: null,
  tokenIndex: null,
  sessionId: null,
  apiBase: localStorage.getItem('oracleApiBase') || 'http://127.0.0.1:8000',
  apiReady: false,
  apiChunks: 0,
};"""

NEW_STATE = """const NavigatorState = {
  history: [],
  mode: 'normal',
  engine: 'local',
  theme: null,
  corpus: null,
  tokenIndex: null,
  sessionId: null,
  apiBase: localStorage.getItem('oracleApiBase') || 'http://127.0.0.1:8000',
  apiReady: false,
  apiChunks: 0,
};

function clearNavigatorHistory() {
  NavigatorState.history = [];
  NavigatorState.sessionId = null;
  try { sessionStorage.removeItem('navHistory'); localStorage.removeItem('navHistory'); } catch (_) {}
  renderNavigatorHistory();
}

function fetchWithTimeout(url, options = {}, ms = 4000) {
  const ctrl = new AbortController();
  const id = setTimeout(() => ctrl.abort(), ms);
  return fetch(url, { ...options, signal: ctrl.signal }).finally(() => clearTimeout(id));
}

function tryGovernanceAnswer(query) {
  const ql = normNav(query);
  if (!/(ceo|cfo|presidente|conselho|conselheiro|pandemia)/.test(ql)) return null;
  const gov = answerGovQuery(query);
  if (!gov || gov.titulo === 'Consulta') return null;
  return {
    titulo: gov.titulo,
    resumoExecutivo: String(gov.texto || '').replace(/<br>/g, '\\n'),
    evidencias: gov.fonte ? [{ periodo: '—', citacao: gov.texto, fonte: gov.fonte, sourceType: 'Governança' }] : [],
    fontes: gov.fonte ? [gov.fonte] : [],
    fontesAgrupadas: gov.fonte ? { 'Governança': [gov.fonte] } : {},
    indicadores: [], conclusoes: [], riscos: [], oportunidades: [],
    confidence: { level: 'alto', label: '🟢 Alta' },
    domain: 'Governança', periodos: [], scanned: NavigatorState.corpus?.length || 0, briefing: null,
  };
}"""

OLD_RUN_NAV = """  const q = String(query || '').trim();
  if (!q) return null;

  if (options.theme) {"""

NEW_RUN_NAV = """  const q = String(query || '').trim();
  if (!q) return null;

  const govAnswer = tryGovernanceAnswer(q);
  if (govAnswer) {
    NavigatorState.history.unshift({ query: q, mode: 'local', engine: 'local', answer: govAnswer, ts: new Date().toISOString() });
    if (NavigatorState.history.length > 30) NavigatorState.history.pop();
    return govAnswer;
  }

  if (options.theme) {"""

OLD_CHECK = r"""async function checkOracleHealth() {
  updateOracleStatus('loading', 'Conectando à IA GPT-4o em ' + NavigatorState.apiBase + '...');
  try {
    const res = await fetch(NavigatorState.apiBase + '/api/health', { method: 'GET' });
    if (!res.ok) throw new Error('HTTP ' + res.status);
    const data = await res.json();
    NavigatorState.apiReady = !!data.index_ready;
    NavigatorState.apiChunks = data.manifest?.total_chunks || 0;
    if (NavigatorState.apiReady) {
      updateOracleStatus('online', 'IA GPT-4o online — Corporate Oracle', NavigatorState.apiChunks);
    } else {
      updateOracleStatus('offline', 'API online, mas indexação pendente — execute scripts\\index.bat', 0);
    }
    return NavigatorState.apiReady;
  } catch (e) {
    NavigatorState.apiReady = false;
    updateOracleStatus('offline', 'IA GPT-4o offline — modos locais do Navigator funcionam sem internet/API', 0);
    return false;
  }
}"""

NEW_CHECK = """async function checkOracleHealth() {
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

OLD_RENDER_NAV_START = """function renderNavigator() {
  document.getElementById('navAnswerArea').innerHTML = renderNavigatorWelcome();
  document.getElementById('navThemeChips').innerHTML = NAV_THEMES.map(t =>
    `<button type="button" class="nav-theme-chip" data-nav-theme="${t.id}">${escNav(t.label)}</button>`).join('');

  renderNavigatorHistory();

  const run = (forcedQuery, opts = {}) => {
    const q = forcedQuery ?? document.getElementById('navQueryInput').value.trim();
    if (!q && !opts.discovery && !opts.briefing) return;
    if (NavigatorState.engine === 'gpt' && !opts.discovery && !opts.briefing) {
      runOracleQuery(q);
      return;
    }
    const answer = runNavigatorQuery(q, {
      deep: NavigatorState.mode === 'deep',
      investigate: NavigatorState.mode === 'investigate',
      briefing: opts.briefing || NavigatorState.mode === 'briefing',
      discovery: opts.discovery,
      theme: NavigatorState.theme,
    });
    document.getElementById('navAnswerArea').innerHTML = renderNavigatorAnswer(answer);
    renderNavigatorHistory();
  };"""

NEW_RENDER_NAV_START = """function renderNavigator() {
  clearNavigatorHistory();
  buildNavigatorCorpus();
  document.getElementById('navAnswerArea').innerHTML = renderNavigatorWelcome();
  document.getElementById('navThemeChips').innerHTML = NAV_THEMES.map(t =>
    `<button type="button" class="nav-theme-chip" data-nav-theme="${t.id}">${escNav(t.label)}</button>`).join('');

  renderNavigatorHistory();

  const runLocal = (q, opts = {}) => {
    const answer = runNavigatorQuery(q, { theme: opts.theme || NavigatorState.theme });
    if (answer) {
      document.getElementById('navAnswerArea').innerHTML = renderNavigatorAnswer(answer);
      renderNavigatorHistory();
    }
  };

  const run = (forcedQuery, opts = {}) => {
    const q = forcedQuery ?? document.getElementById('navQueryInput').value.trim();
    if (!q) return;
    if (NavigatorState.engine === 'gpt' && NavigatorState.apiReady) {
      runOracleQuery(q).catch(() => runLocal(q, opts));
      return;
    }
    runLocal(q, opts);
  };"""

OLD_THEME_CLICK = """  document.getElementById('navThemeChips').onclick = e => {
    const chip = e.target.closest('[data-nav-theme]');
    if (!chip) return;
    NavigatorState.mode = 'investigate';
    NavigatorState.theme = chip.dataset.navTheme;
    document.querySelectorAll('.nav-mode-btn').forEach(b => b.classList.remove('active'));
    document.getElementById('navModeInvestigate')?.classList.add('active');
    const th = NAV_THEMES.find(t => t.id === chip.dataset.navTheme);
    document.getElementById('navQueryInput').value = th ? th.label : '';
    run(th ? th.label : '');
  };

  const setEngine = (engine) => {
    NavigatorState.engine = engine;
    document.querySelectorAll('.nav-mode-btn').forEach(b => b.classList.remove('active'));
    if (engine === 'gpt') {
      document.getElementById('navModeGpt')?.classList.add('active');
      NavigatorState.mode = 'normal';
    }
  };

  const setMode = (mode) => {
    NavigatorState.engine = 'local';
    NavigatorState.mode = mode;
    document.querySelectorAll('.nav-mode-btn').forEach(b => b.classList.remove('active'));
    const ids = { deep: 'navModeDeep', investigate: 'navModeInvestigate', briefing: 'navModeBriefing', discovery: 'navModeDiscover' };
    if (ids[mode]) document.getElementById(ids[mode])?.classList.add('active');
    if (mode === 'briefing') run(document.getElementById('navQueryInput').value || 'Executive Briefing CVC Corp', { briefing: true });
    if (mode === 'discovery') run('', { discovery: true });
  };

  document.getElementById('navModeGpt').onclick = () => setEngine('gpt');
  document.getElementById('navModeDeep').onclick = () => setMode('deep');
  document.getElementById('navModeInvestigate').onclick = () => { NavigatorState.theme = null; setMode('investigate'); };
  document.getElementById('navModeBriefing').onclick = () => setMode('briefing');
  document.getElementById('navModeDiscover')?.addEventListener('click', () => setMode('discovery'));
  checkOracleHealth();
}"""

NEW_THEME_CLICK = """  document.getElementById('navThemeChips').onclick = e => {
    const chip = e.target.closest('[data-nav-theme]');
    if (!chip) return;
    NavigatorState.theme = chip.dataset.navTheme;
    const th = NAV_THEMES.find(t => t.id === chip.dataset.navTheme);
    document.getElementById('navQueryInput').value = th ? th.label : '';
    run(th ? th.label : '', { theme: chip.dataset.navTheme });
  };

  checkOracleHealth();
}

window.addEventListener('pageshow', () => {
  clearNavigatorHistory();
});"""

OLD_ORACLE_CATCH = r"""  } catch (err) {
    textEl.innerHTML = `<span style="color:var(--danger)">Erro: ${escNav(err.message)}</span><br><br>
      <span style="color:var(--muted);font-size:0.82rem">Verifique se a API está rodando (<code>scripts\\start-api.bat</code>), se a base foi indexada (<code>scripts\\index.bat</code>) e se o <code>.env</code> contém OPENAI_API_KEY.</span>`;
    confEl.textContent = '❌ Erro';
  } finally {"""

NEW_ORACLE_CATCH = """  } catch (err) {
    NavigatorState.engine = 'local';
    const answer = runNavigatorQuery(q, {});
    if (answer) {
      document.getElementById('navAnswerArea').innerHTML = renderNavigatorAnswer(answer);
      renderNavigatorHistory();
      updateOracleStatus('online', 'Consultor local ativo — GPT-4o indisponível', 0);
      return;
    }
    textEl.innerHTML = `<span style="color:var(--danger)">Erro: ${escNav(err.message)}</span>`;
    confEl.textContent = '❌ Erro';
  } finally {"""


def main() -> None:
    html = HTML.read_text(encoding="utf-8")
    before = html.count("\n") + 1
    assert "decodeKbPayload" in html

    replacements = [
        (OLD_BUTTONS, NEW_BUTTONS),
        (OLD_STATUS, NEW_STATUS),
        (OLD_STATE, NEW_STATE),
        (OLD_RUN_NAV, NEW_RUN_NAV),
        (OLD_CHECK, NEW_CHECK),
        (OLD_RENDER_NAV_START, NEW_RENDER_NAV_START),
        (OLD_THEME_CLICK, NEW_THEME_CLICK),
        (OLD_ORACLE_CATCH, NEW_ORACLE_CATCH),
    ]
    for old, new in replacements:
        assert old in html, f"Trecho não encontrado: {old[:60]}..."
        html = html.replace(old, new, 1)

    assert "navModeDeep" not in html
    assert "clearNavigatorHistory" in html
    assert "tryGovernanceAnswer" in html
    after = html.count("\n") + 1
    assert abs(after - before) < 80, f"Linhas mudaram demais: {before} -> {after}"

    HTML.write_text(html, encoding="utf-8")
    print(f"OK — {after} linhas, {HTML.stat().st_size / (1024 * 1024):.2f} MB")


if __name__ == "__main__":
    main()
