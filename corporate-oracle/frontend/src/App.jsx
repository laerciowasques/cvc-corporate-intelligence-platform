import { useCallback, useEffect, useRef, useState } from 'react'
import ReactMarkdown from 'react-markdown'

const SUGGESTIONS = [
  'Quem era o CEO em 2019?',
  'Quem foram todos os CFOs da companhia?',
  'Resuma os resultados do 4T23.',
  'O que foi dito sobre margem EBITDA em 2024?',
  'Quais riscos foram mencionados pelo management?',
]

function EvidenceCard({ ev }) {
  return (
    <div className="rounded-lg border border-gray-700 bg-surface-2 p-3 text-sm light:border-gray-200 light:bg-white">
      <div className="mb-1 flex flex-wrap gap-2 text-xs text-gray-400">
        <span className="rounded bg-surface px-2 py-0.5 light:bg-gray-100">{ev.document_type || 'doc'}</span>
        {ev.period && <span>{ev.period}</span>}
        {ev.date && <span>{ev.date}</span>}
        {ev.score != null && <span>score {ev.score}</span>}
      </div>
      <p className="font-medium text-accent2">{ev.document_title}</p>
      <p className="mt-2 text-gray-400 light:text-gray-600">{ev.excerpt}</p>
      {ev.fonte && <p className="mt-1 text-xs text-gray-500">Fonte: {ev.fonte}</p>}
    </div>
  )
}

export default function App() {
  const [theme, setTheme] = useState(() => localStorage.getItem('theme') || 'dark')
  const [sessions, setSessions] = useState([])
  const [sessionId, setSessionId] = useState(null)
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [evidences, setEvidences] = useState([])
  const [followUps, setFollowUps] = useState([])
  const [mode, setMode] = useState('chat')
  const [searchResults, setSearchResults] = useState([])
  const [health, setHealth] = useState(null)
  const bottomRef = useRef(null)

  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark')
    document.documentElement.classList.toggle('light', theme === 'light')
    localStorage.setItem('theme', theme)
  }, [theme])

  const loadSessions = useCallback(async () => {
    const res = await fetch('/api/sessions')
    if (res.ok) setSessions(await res.json())
  }, [])

  const loadHealth = useCallback(async () => {
    const res = await fetch('/api/health')
    if (res.ok) setHealth(await res.json())
  }, [])

  useEffect(() => {
    loadSessions()
    loadHealth()
  }, [loadSessions, loadHealth])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const loadSession = async (id) => {
    setSessionId(id)
    setEvidences([])
    setFollowUps([])
    const res = await fetch(`/api/sessions/${id}/messages`)
    if (res.ok) {
      const data = await res.json()
      setMessages(data.messages || [])
    }
  }

  const newChat = async () => {
    const res = await fetch('/api/sessions', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' })
    if (res.ok) {
      const data = await res.json()
      setSessionId(data.id)
      setMessages([])
      setEvidences([])
      setFollowUps([])
      loadSessions()
    }
  }

  const sendMessage = async (text) => {
    const msg = (text || input).trim()
    if (!msg || loading) return
    setInput('')
    setLoading(true)
    setEvidences([])
    setFollowUps([])
    setMessages((m) => [...m, { role: 'user', content: msg }])
    setMessages((m) => [...m, { role: 'assistant', content: '' }])

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: msg, session_id: sessionId, stream: true }),
      })

      if (!res.ok) throw new Error(await res.text())

      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      let currentSession = sessionId

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const parts = buffer.split('\n\n')
        buffer = parts.pop() || ''

        for (const part of parts) {
          const lines = part.split('\n')
          let event = 'message'
          let data = ''
          for (const line of lines) {
            if (line.startsWith('event:')) event = line.slice(6).trim()
            if (line.startsWith('data:')) data = line.slice(5).trim()
          }
          if (!data) continue
          const payload = JSON.parse(data)
          if (event === 'meta') {
            setEvidences(payload.evidences || [])
            setFollowUps(payload.follow_up_suggestions || [])
          } else if (event === 'token') {
            setMessages((prev) => {
              const copy = [...prev]
              const last = copy[copy.length - 1]
              if (last?.role === 'assistant') {
                copy[copy.length - 1] = { ...last, content: last.content + payload.content }
              }
              return copy
            })
          } else if (event === 'done') {
            currentSession = payload.session_id
            setSessionId(payload.session_id)
            loadSessions()
          }
        }
      }
      if (!currentSession) loadSessions()
    } catch (err) {
      setMessages((m) => {
        const copy = [...m]
        copy[copy.length - 1] = { role: 'assistant', content: `Erro: ${err.message}` }
        return copy
      })
    } finally {
      setLoading(false)
    }
  }

  const quickSearch = async () => {
    const q = input.trim()
    if (!q) return
    setMode('search')
    const res = await fetch('/api/search', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: q, top_k: 8 }),
    })
    if (res.ok) setSearchResults(await res.json())
    else setSearchResults([])
  }

  return (
    <div className="flex h-screen overflow-hidden">
      <aside className="flex w-64 shrink-0 flex-col border-r border-gray-800 bg-black light:border-gray-200 light:bg-white">
        <div className="border-b border-gray-800 p-4 light:border-gray-200">
          <h1 className="text-sm font-semibold text-accent">Corporate Oracle</h1>
          <p className="text-xs text-gray-500">CVC Corp · Base RI</p>
        </div>
        <div className="p-3">
          <button
            onClick={newChat}
            className="w-full rounded-lg border border-accent/40 bg-accent/10 px-3 py-2 text-sm text-accent hover:bg-accent/20"
          >
            + Nova conversa
          </button>
        </div>
        <div className="flex-1 overflow-y-auto px-2 pb-2">
          {sessions.map((s) => (
            <button
              key={s.id}
              onClick={() => { setMode('chat'); loadSession(s.id) }}
              className={`mb-1 w-full rounded-lg px-3 py-2 text-left text-xs transition ${
                sessionId === s.id ? 'bg-accent/15 text-accent' : 'text-gray-400 hover:bg-surface-2 light:hover:bg-gray-100'
              }`}
            >
              <span className="line-clamp-2">{s.title}</span>
            </button>
          ))}
        </div>
        <div className="border-t border-gray-800 p-3 text-xs text-gray-500 light:border-gray-200">
          {health?.index_ready ? (
            <span className="text-accent">● Índice pronto ({health.manifest?.total_chunks} chunks)</span>
          ) : (
            <span className="text-amber-400">● Indexação pendente</span>
          )}
        </div>
      </aside>

      <main className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center justify-between border-b border-gray-800 px-6 py-3 light:border-gray-200">
          <div className="flex gap-2">
            <button
              onClick={() => setMode('chat')}
              className={`rounded px-3 py-1 text-sm ${mode === 'chat' ? 'bg-accent/15 text-accent' : 'text-gray-400'}`}
            >
              Chat
            </button>
            <button
              onClick={() => setMode('search')}
              className={`rounded px-3 py-1 text-sm ${mode === 'search' ? 'bg-accent2/15 text-accent2' : 'text-gray-400'}`}
            >
              Pesquisa rápida
            </button>
          </div>
          <button
            onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
            className="rounded border border-gray-700 px-3 py-1 text-xs light:border-gray-300"
          >
            {theme === 'dark' ? '☀ Claro' : '🌙 Escuro'}
          </button>
        </header>

        {mode === 'chat' ? (
          <>
            <div className="flex-1 overflow-y-auto px-4 py-6 md:px-8">
              {messages.length === 0 && (
                <div className="mx-auto max-w-2xl text-center">
                  <h2 className="mb-2 text-xl font-semibold">Consulta Documental CVC Corp</h2>
                  <p className="mb-6 text-sm text-gray-400">Pergunte sobre governança, resultados, riscos, fatos relevantes e estratégia.</p>
                  <div className="flex flex-wrap justify-center gap-2">
                    {SUGGESTIONS.map((s) => (
                      <button
                        key={s}
                        onClick={() => sendMessage(s)}
                        className="rounded-full border border-gray-700 px-3 py-1.5 text-xs text-gray-300 hover:border-accent light:border-gray-300 light:text-gray-700"
                      >
                        {s}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              <div className="mx-auto max-w-3xl space-y-6">
                {messages.map((m, i) => (
                  <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                    <div
                      className={`max-w-[85%] rounded-2xl px-4 py-3 ${
                        m.role === 'user'
                          ? 'bg-accent/20 text-gray-100 light:text-gray-900'
                          : 'bg-surface-2 light:bg-white light:shadow-sm'
                      }`}
                    >
                      {m.role === 'assistant' ? (
                        <div className="prose-chat text-sm">
                          <ReactMarkdown>{m.content || (loading && i === messages.length - 1 ? '...' : '')}</ReactMarkdown>
                        </div>
                      ) : (
                        <p className="text-sm">{m.content}</p>
                      )}
                    </div>
                  </div>
                ))}

                {evidences.length > 0 && (
                  <div className="space-y-2">
                    <h3 className="text-xs font-semibold uppercase tracking-wide text-accent2">Evidências</h3>
                    {evidences.map((ev, i) => (
                      <EvidenceCard key={i} ev={ev} />
                    ))}
                  </div>
                )}

                {followUps.length > 0 && !loading && (
                  <div className="flex flex-wrap gap-2">
                    {followUps.map((f) => (
                      <button
                        key={f}
                        onClick={() => sendMessage(f)}
                        className="rounded-full border border-accent2/40 px-3 py-1 text-xs text-accent2 hover:bg-accent2/10"
                      >
                        {f}
                      </button>
                    ))}
                  </div>
                )}
                <div ref={bottomRef} />
              </div>
            </div>

            <div className="border-t border-gray-800 p-4 light:border-gray-200">
              <form
                className="mx-auto flex max-w-3xl gap-2"
                onSubmit={(e) => { e.preventDefault(); sendMessage() }}
              >
                <input
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Ex.: Quem era o CFO em 2019?"
                  disabled={loading}
                  className="flex-1 rounded-xl border border-gray-700 bg-surface px-4 py-3 text-sm outline-none focus:border-accent light:border-gray-300 light:bg-white"
                />
                <button
                  type="submit"
                  disabled={loading || !input.trim()}
                  className="rounded-xl bg-accent px-5 py-3 text-sm font-medium text-black disabled:opacity-40"
                >
                  {loading ? '...' : 'Enviar'}
                </button>
              </form>
            </div>
          </>
        ) : (
          <div className="flex flex-1 flex-col overflow-hidden p-6">
            <form
              className="mx-auto mb-4 flex w-full max-w-3xl gap-2"
              onSubmit={(e) => { e.preventDefault(); quickSearch() }}
            >
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Busca por palavra-chave ou semântica (sem LLM)..."
                className="flex-1 rounded-xl border border-gray-700 bg-surface px-4 py-3 text-sm light:border-gray-300 light:bg-white"
              />
              <button type="submit" className="rounded-xl bg-accent2 px-5 py-3 text-sm text-white">Buscar</button>
            </form>
            <div className="mx-auto w-full max-w-3xl flex-1 space-y-3 overflow-y-auto">
              {searchResults.map((hit) => (
                <div key={hit.chunk_id} className="rounded-lg border border-gray-700 bg-surface-2 p-4 light:border-gray-200 light:bg-white">
                  <div className="mb-1 text-xs text-gray-500">score {hit.score} · {hit.metadata?.document_type} · {hit.metadata?.period}</div>
                  <p className="text-sm">{hit.text.slice(0, 500)}{hit.text.length > 500 ? '...' : ''}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
