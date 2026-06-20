/** Status da camada LLM (Vercel). A base documental fica no browser. */
module.exports = async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  if (req.method === 'OPTIONS') return res.status(204).end();
  if (req.method !== 'GET') return res.status(405).json({ error: 'Method not allowed' });

  const hasKey = !!process.env.OPENAI_API_KEY;
  res.status(200).json({
    index_ready: hasKey,
    api_ready: hasKey,
    engine: process.env.OPENAI_MODEL || 'gpt-4o',
    mode: 'hybrid-rag',
    manifest: { total_chunks: 'client-side', provider: 'openai' },
  });
};
