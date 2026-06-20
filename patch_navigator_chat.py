"""Corrige crash do Navigator (narrativa_evolucao) e adiciona chat funcional."""
from pathlib import Path

HTML = Path(__file__).parent / "CVC_Corporate_Intelligence_Platform.html"

CSS_ADD = """
.nav-chat-thread { margin-top: 0.75rem; padding: 1rem; min-height: 280px; max-height: calc(100vh - 340px); overflow-y: auto; display: flex; flex-direction: column; gap: 0.75rem; background: var(--bg2); border: 1px solid var(--border); border-radius: var(--radius); }
.nav-msg { display: flex; max-width: 92%; }
.nav-msg-user { align-self: flex-end; justify-content: flex-end; }
.nav-msg-bot { align-self: flex-start; }
.nav-msg-bubble { padding: 0.65rem 0.85rem; border-radius: 12px; font-size: 0.86rem; line-height: 1.55; }
.nav-msg-user .nav-msg-bubble { background: rgba(61,139,253,0.18); border: 1px solid rgba(61,139,253,0.35); color: var(--text); border-bottom-right-radius: 4px; }
.nav-msg-bot .nav-msg-bubble { background: var(--bg3); border: 1px solid var(--border); color: var(--text); border-bottom-left-radius: 4px; }
.nav-msg-bot .nav-msg-bubble p { margin: 0 0 0.5rem; }
.nav-msg-bot .nav-msg-bubble p:last-child { margin-bottom: 0; }
.nav-chat-evidence { margin-top: 0.5rem; padding-top: 0.5rem; border-top: 1px solid var(--border); color: var(--muted); font-size: 0.78rem; line-height: 1.45; }
.nav-chat-meta { display: block; margin-top: 0.45rem; color: var(--muted); font-size: 0.72rem; }
.nav-msg-typing .nav-msg-bubble { color: var(--muted); font-style: italic; }
"""

OLD_NARRATIVA = """  (KB.narrativa_evolucao || []).forEach((n, i) => addChunk(chunks, seen, {
    id: `nar-${i}`, tipo: 'narrativa', titulo: n.titulo || n.periodo, texto: [n.titulo, n.texto, n.resumo].filter(Boolean).join(' '), fonte: n.fonte, periodo: n.periodo,
  }));"""

NEW_NARRATIVA = """  const navEvo = KB.narrativa_evolucao;
  if (navEvo && typeof navEvo === 'object') {
    addChunk(chunks, seen, {
      id: 'nar-sintese', tipo: 'narrativa', titulo: navEvo.titulo || 'Narrativa Executiva',
      texto: [navEvo.titulo, navEvo.sintese].filter(Boolean).join(' '),
      fonte: 'Narrativa Executiva', periodo: '2013–2026',
    });
    (navEvo.capitulos || []).forEach((c, i) => addChunk(chunks, seen, {
      id: `nar-cap-${i}`, tipo: 'narrativa', titulo: c.titulo || c.periodo,
      texto: [c.tese, ...(c.destaques || [])].filter(Boolean).join(' '),
      fonte: 'Narrativa Executiva', periodo: c.periodo,
    }));
  }"""

OLD_ANSWER_DIV = '            <div id="navAnswerArea"></div>'

NEW_ANSWER_DIV = '            <div id="navChatThread" class="nav-chat-thread"></div>'

OLD_STATE_END = """  apiReady: false,
  apiChunks: 0,
};"""

NEW_STATE_END = """  apiReady: false,
  apiChunks: 0,
  chatMessages: [],
};"""

OLD_CLEAR = """function clearNavigatorHistory() {
  NavigatorState.history = [];
  NavigatorState.sessionId = null;
  try { sessionStorage.removeItem('navHistory'); localStorage.removeItem('navHistory'); } catch (_) {}
  renderNavigatorHistory();
}"""

NEW_CLEAR = """function clearNavigatorHistory() {
  NavigatorState.history = [];
  NavigatorState.sessionId = null;
  NavigatorState.chatMessages = [];
  try { sessionStorage.removeItem('navHistory'); localStorage.removeItem('navHistory'); } catch (_) {}
  renderNavigatorHistory();
  renderChatThread();
}

function formatChatAnswer(answer) {
  if (!answer) return '<p>Não encontrei informações na base de conhecimento.</p>';
  let html = `<p>${escNav(answer.resumoExecutivo || answer.resumo || '').replace(/\\n/g, '<br>')}</p>`;
  const ev = (answer.evidencias || []).slice(0, 3);
  if (ev.length) {
    html += `<div class="nav-chat-evidence">${ev.map(e =>
      `<div><span class="tag">${escNav(e.sourceType || e.tipo || 'doc')}${e.periodo ? ' · ' + escNav(e.periodo) : ''}</span> ${escNav((e.citacao || e.texto || '').slice(0, 220))}${(e.citacao || e.texto || '').length > 220 ? '…' : ''}</div>`
    ).join('')}</div>`;
  }
  const conf = typeof answer.confidence === 'string' ? answer.confidence : answer.confidence?.label;
  if (conf) html += `<small class="nav-chat-meta">${escNav(conf)}</small>`;
  return html;
}

function renderChatThread() {
  const el = document.getElementById('navChatThread');
  if (!el) return;
  if (!NavigatorState.chatMessages.length) {
    el.innerHTML = `<div class="nav-msg nav-msg-bot"><div class="nav-msg-bubble"><p>Olá! Sou o consultor corporativo CVC. Pergunte em linguagem natural sobre resultados, governança, estratégia ou histórico (2013–2026).</p><p style="color:var(--muted);font-size:0.78rem;margin-top:0.5rem">Ex.: <em>Quem era o CEO em 2020?</em> · <em>Qual foi o EBITDA do 1T26?</em></p></div></div>`;
    return;
  }
  el.innerHTML = NavigatorState.chatMessages.map(m => {
    const cls = m.role === 'user' ? 'nav-msg-user' : 'nav-msg-bot' + (m.typing ? ' nav-msg-typing' : '');
    const body = m.role === 'user' ? escNav(m.text) : m.html || escNav(m.text || '');
    return `<div class="nav-msg ${cls}"><div class="nav-msg-bubble">${body}</div></div>`;
  }).join('');
  el.scrollTop = el.scrollHeight;
}

function appendChatMessage(role, text, html, typing) {
  NavigatorState.chatMessages.push({ role, text, html, typing: !!typing });
  renderChatThread();
}

function removeLastChatMessage() {
  if (NavigatorState.chatMessages.length) NavigatorState.chatMessages.pop();
}

async function runChatQuery(forcedQuery) {
  const q = (forcedQuery ?? document.getElementById('navQueryInput')?.value ?? '').trim();
  if (!q) return;
  const btn = document.getElementById('navQueryBtn');
  if (btn) btn.disabled = true;
  appendChatMessage('user', q);
  document.getElementById('navQueryInput').value = '';
  appendChatMessage('bot', 'Analisando base de conhecimento…', null, true);
  await new Promise(r => setTimeout(r, 20));
  try {
    if (!NavigatorState.corpus) buildNavigatorCorpus();
    if (NavigatorState.engine === 'gpt' && NavigatorState.apiReady) {
      await runOracleQuery(q);
      return;
    }
    const answer = runNavigatorQuery(q, { theme: NavigatorState.theme });
    removeLastChatMessage();
    appendChatMessage('bot', '', formatChatAnswer(answer));
    renderNavigatorHistory();
  } catch (err) {
    removeLastChatMessage();
    appendChatMessage('bot', 'Erro ao processar: ' + (err.message || err));
  } finally {
    if (btn) btn.disabled = false;
  }
}"""

OLD_RENDER_NAV = """function renderNavigator() {
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
  };

  document.getElementById('navQueryBtn').onclick = () => run();
  document.getElementById('navQueryInput').onkeydown = e => { if (e.key === 'Enter') run(); };

  document.getElementById('navAnswerArea').addEventListener('click', e => {"""

NEW_RENDER_NAV = """function renderNavigator() {
  clearNavigatorHistory();
  updateOracleStatus('online', 'Consultor pronto — carregando índice local…', 0);
  renderChatThread();
  document.getElementById('navThemeChips').innerHTML = NAV_THEMES.map(t =>
    `<button type="button" class="nav-theme-chip" data-nav-theme="${t.id}">${escNav(t.label)}</button>`).join('');

  renderNavigatorHistory();

  setTimeout(() => {
    try {
      buildNavigatorCorpus();
      updateOracleStatus('online', 'Consultor pronto — ' + NavigatorState.corpus.length + ' registros indexados', NavigatorState.corpus.length);
    } catch (err) {
      console.error(err);
      updateOracleStatus('offline', 'Erro ao indexar base: ' + err.message, 0);
    }
  }, 30);

  document.getElementById('navQueryBtn').onclick = () => runChatQuery();
  document.getElementById('navQueryInput').onkeydown = e => { if (e.key === 'Enter') runChatQuery(); };

  document.getElementById('navChatThread').addEventListener('click', e => {"""

OLD_ORACLE_RUN = """async function runOracleQuery(query) {
  const q = (query || '').trim();
  if (!q) return;
  const area = document.getElementById('navAnswerArea');
  area.innerHTML = renderOracleAnswerShell(q, true);"""

NEW_ORACLE_RUN = """async function runOracleQuery(query) {
  const q = (query || '').trim();
  if (!q) return;
  removeLastChatMessage();
  appendChatMessage('bot', 'Consultando IA GPT-4o…', null, true);"""

OLD_ORACLE_END = """    textEl.innerHTML = escNav(fullText).replace(/\\n/g, '<br>');
    NavigatorState.history.unshift({
      query: q, mode: 'gpt-4o', engine: 'gpt', answer: { resumoExecutivo: fullText, confidence: meta.confidence, evidencias: meta.evidences, titulo: q },
      ts: new Date().toISOString(),
    });
    if (NavigatorState.history.length > 30) NavigatorState.history.pop();
    renderNavigatorHistory();

  } catch (err) {
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
  } finally {
    document.getElementById('navQueryBtn').disabled = false;
  }
}"""

NEW_ORACLE_END = """    removeLastChatMessage();
    appendChatMessage('bot', '', escNav(fullText).replace(/\\n/g, '<br>'));
    NavigatorState.history.unshift({
      query: q, mode: 'gpt-4o', engine: 'gpt', answer: { resumoExecutivo: fullText, confidence: meta.confidence, evidencias: meta.evidences, titulo: q },
      ts: new Date().toISOString(),
    });
    if (NavigatorState.history.length > 30) NavigatorState.history.pop();
    renderNavigatorHistory();

  } catch (err) {
    NavigatorState.engine = 'local';
    removeLastChatMessage();
    const answer = runNavigatorQuery(q, {});
    if (answer) {
      appendChatMessage('bot', '', formatChatAnswer(answer));
      renderNavigatorHistory();
      updateOracleStatus('online', 'Consultor local ativo — GPT-4o indisponível', 0);
      return;
    }
    appendChatMessage('bot', 'Erro: ' + (err.message || err));
  } finally {
    document.getElementById('navQueryBtn').disabled = false;
  }
}"""

# Fix oracle query middle - remove references to textEl at start since we changed structure
OLD_ORACLE_MID = """  const textEl = document.getElementById('navOracleText');
  const confEl = document.getElementById('navOracleConf');
  const evidEl = document.getElementById('navOracleEvidences');
  const followEl = document.getElementById('navOracleFollowups');
  document.getElementById('navQueryBtn').disabled = true;

  let fullText = '';
  let meta = { confidence: 'medium', evidences: [], follow_up_suggestions: [] };"""

NEW_ORACLE_MID = """  document.getElementById('navQueryBtn').disabled = true;

  let fullText = '';
  let meta = { confidence: 'medium', evidences: [], follow_up_suggestions: [] };"""

OLD_ORACLE_TOKEN = """        } else if (event === 'token') {
          fullText += payload.content || '';
          textEl.innerHTML = escNav(fullText).replace(/\\n/g, '<br>') + '<span class="nav-oracle-cursor"></span>';
        } else if (event === 'done') {"""

NEW_ORACLE_TOKEN = """        } else if (event === 'token') {
          fullText += payload.content || '';
        } else if (event === 'done') {"""

OLD_ORACLE_META = """        if (event === 'meta') {
          meta = payload;
          confEl.textContent = ORACLE_CONF_LABELS[payload.confidence] || payload.confidence;
          evidEl.innerHTML = renderOracleEvidences(payload.evidences);
          followEl.innerHTML = renderOracleFollowups(payload.follow_up_suggestions);
        } else if (event === 'token') {"""

NEW_ORACLE_META = """        if (event === 'meta') {
          meta = payload;
        } else if (event === 'token') {"""

OLD_THEME_RUN = """    run(th ? th.label : '', { theme: chip.dataset.navTheme });
  };

  checkOracleHealth();
}"""

NEW_THEME_RUN = """    runChatQuery(th ? th.label : '');
  };

  checkOracleHealth();
}"""

OLD_CHIP_RUN = """    if (chip) { document.getElementById('navQueryInput').value = chip.dataset.navQ; NavigatorState.mode = 'normal'; run(chip.dataset.navQ); return; }"""

NEW_CHIP_RUN = """    if (chip) { document.getElementById('navQueryInput').value = chip.dataset.navQ; NavigatorState.mode = 'normal'; runChatQuery(chip.dataset.navQ); return; }"""

OLD_ORACLE_Q = """      runOracleQuery(oracleQ.dataset.oracleQ);
      return;"""

NEW_ORACLE_Q = """      runChatQuery(oracleQ.dataset.oracleQ);
      return;"""

OLD_HIST_CLICK = """    if (h.engine === 'gpt') {
      document.getElementById('navAnswerArea').innerHTML = renderOracleAnswerShell(h.query, false);
      document.getElementById('navOracleText').innerHTML = escNav(h.answer.resumoExecutivo || '').replace(/\\n/g, '<br>');
      document.getElementById('navOracleConf').textContent = ORACLE_CONF_LABELS[h.answer.confidence] || h.answer.confidence || '';
      document.getElementById('navOracleEvidences').innerHTML = renderOracleEvidences(h.answer.evidencias);
    } else {
      document.getElementById('navAnswerArea').innerHTML = renderNavigatorAnswer(h.answer);
    }"""

NEW_HIST_CLICK = """    NavigatorState.chatMessages = [
      { role: 'user', text: h.query },
      { role: 'bot', text: '', html: h.engine === 'gpt'
        ? escNav(h.answer.resumoExecutivo || '').replace(/\\n/g, '<br>')
        : formatChatAnswer(h.answer) }
    ];
    renderChatThread();"""

OLD_STATUS_HTML = """              <div id="navOracleStatus" class="nav-oracle-status">
                <span class="dot loading"></span>
                <span>Inicializando consultor...</span>
              </div>"""

NEW_STATUS_HTML = """              <div id="navOracleStatus" class="nav-oracle-status">
                <span class="dot online"></span>
                <span>Consultor pronto</span>
              </div>"""

OLD_PLATFORM = "<h1>Corporate Intelligence Plataform</h1>"

NEW_PLATFORM = "<h1>Corporate Intelligence Platform</h1>"


def main() -> None:
    html = HTML.read_text(encoding="utf-8")
    before = html.count("\n") + 1

    if ".nav-chat-thread" not in html:
        html = html.replace(".nav-welcome { margin-bottom: 0.5rem; }", ".nav-welcome { margin-bottom: 0.5rem; }" + CSS_ADD, 1)

    replacements = [
        (OLD_NARRATIVA, NEW_NARRATIVA),
        (OLD_ANSWER_DIV, NEW_ANSWER_DIV),
        (OLD_STATE_END, NEW_STATE_END),
        (OLD_CLEAR, NEW_CLEAR),
        (OLD_RENDER_NAV, NEW_RENDER_NAV),
        (OLD_ORACLE_RUN, NEW_ORACLE_RUN),
        (OLD_ORACLE_MID, NEW_ORACLE_MID),
        (OLD_ORACLE_META, NEW_ORACLE_META),
        (OLD_ORACLE_TOKEN, NEW_ORACLE_TOKEN),
        (OLD_ORACLE_END, NEW_ORACLE_END),
        (OLD_THEME_RUN, NEW_THEME_RUN),
        (OLD_CHIP_RUN, NEW_CHIP_RUN),
        (OLD_ORACLE_Q, NEW_ORACLE_Q),
        (OLD_HIST_CLICK, NEW_HIST_CLICK),
        (OLD_STATUS_HTML, NEW_STATUS_HTML),
        (OLD_PLATFORM, NEW_PLATFORM),
    ]
    for old, new in replacements:
        if old not in html:
            raise AssertionError(f"Trecho não encontrado: {old[:70]}...")
        html = html.replace(old, new, 1)

    assert "navChatThread" in html
    assert "runChatQuery" in html
    assert "navEvo.capitulos" in html
    after = html.count("\n") + 1
    assert abs(after - before) < 120

    HTML.write_text(html, encoding="utf-8")
    print(f"OK — {after} linhas, {HTML.stat().st_size / (1024 * 1024):.2f} MB")


if __name__ == "__main__":
    main()
