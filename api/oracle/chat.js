const OpenAI = require('openai').default;

const SYSTEM_PROMPT = `Você é um analista sênior de RI da CVC Corp. Responda APENAS com base nas evidências fornecidas.
Regras: não invente fatos; cite período/fonte; português executivo; se insuficiente, diga claramente.
Para análises profundas: estruture em (1) resposta direta, (2) contexto/evolução, (3) implicações, (4) fontes.`;

function formatEvidences(evidences) {
  if (!evidences?.length) return '(nenhuma evidência enviada pelo cliente)';
  return evidences.slice(0, 12).map((e, i) => {
    const head = `[${i + 1}] ${e.sourceType || e.tipo || 'Documento'} · ${e.periodo || '—'}`;
    const body = (e.citacao || e.excerpt || e.texto || '').slice(0, 1200);
    const src = e.fonte ? `Fonte: ${e.fonte}` : '';
    return `${head}\n${body}\n${src}`.trim();
  }).join('\n\n');
}

module.exports = async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  if (req.method === 'OPTIONS') return res.status(204).end();
  if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' });

  const apiKey = process.env.OPENAI_API_KEY;
  if (!apiKey) {
    return res.status(503).json({
      error: 'OPENAI_API_KEY não configurada. Adicione a variável no projeto Vercel (Settings → Environment Variables).',
    });
  }

  const { message, evidences = [], history = [], stream = false } = req.body || {};
  const q = String(message || '').trim();
  if (!q) return res.status(400).json({ error: 'message obrigatório' });

  const historyMsgs = (history || []).slice(-6).map(h => ({
    role: h.role === 'assistant' ? 'assistant' : 'user',
    content: String(h.content || '').slice(0, 2000),
  }));

  const userContent = `Pergunta:\n${q}\n\nEvidências recuperadas da base CVC (2013–2026):\n${formatEvidences(evidences)}`;

  const openai = new OpenAI({ apiKey });
  const model = process.env.OPENAI_MODEL || 'gpt-4o';

  try {
    if (stream) {
      res.setHeader('Content-Type', 'text/event-stream');
      res.setHeader('Cache-Control', 'no-cache');
      res.setHeader('Connection', 'keep-alive');

      const confidence = evidences.length >= 4 ? 'high' : evidences.length >= 1 ? 'medium' : 'low';
      res.write(`event: meta\ndata: ${JSON.stringify({
        confidence,
        evidences: evidences.slice(0, 8),
        follow_up_suggestions: [],
      })}\n\n`);

      const streamResp = await openai.chat.completions.create({
        model,
        temperature: 0.2,
        max_tokens: 1800,
        stream: true,
        messages: [
          { role: 'system', content: SYSTEM_PROMPT },
          ...historyMsgs,
          { role: 'user', content: userContent },
        ],
      });

      let full = '';
      for await (const part of streamResp) {
        const token = part.choices[0]?.delta?.content || '';
        if (token) {
          full += token;
          res.write(`event: token\ndata: ${JSON.stringify({ content: token })}\n\n`);
        }
      }
      res.write(`event: done\ndata: ${JSON.stringify({ answer: full })}\n\n`);
      return res.end();
    }

    const completion = await openai.chat.completions.create({
      model,
      temperature: 0.2,
      max_tokens: 1800,
      messages: [
        { role: 'system', content: SYSTEM_PROMPT },
        ...historyMsgs,
        { role: 'user', content: userContent },
      ],
    });

    const answer = completion.choices[0]?.message?.content || '';
    return res.status(200).json({
      answer,
      confidence: evidences.length >= 4 ? 'high' : evidences.length >= 1 ? 'medium' : 'low',
      evidences: evidences.slice(0, 8),
      follow_up_suggestions: [],
    });
  } catch (err) {
    console.error('oracle/chat error', err);
    return res.status(500).json({ error: err.message || 'Erro OpenAI' });
  }
};
