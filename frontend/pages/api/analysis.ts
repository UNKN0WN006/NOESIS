// API proxy: forwards analysis requests from Next.js to the FastAPI backend.
import type { NextApiRequest, NextApiResponse } from 'next'

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  const backend = process.env.BACKEND_URL || 'http://localhost:8000'
  
  try {
    if (req.method === 'POST') {
      const { repo_url } = req.body
      if (!repo_url) {
        return res.status(400).json({ error: 'repo_url is required' })
      }

      const initResponse = await fetch(`${backend}/api/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ repo_url }),
      })

      if (!initResponse.ok) {
        const error = await initResponse.text()
        return res.status(initResponse.status).json({ error })
      }

      const data = await initResponse.json()
      return res.status(200).json(data)
    }

    if (req.method === 'GET') {
      const { session_id, action } = req.query

      if (!session_id || typeof session_id !== 'string') {
        return res.status(400).json({ error: 'session_id query parameter required' })
      }

      const act = action === 'result' ? 'result' : 'progress'
      const endpoint = `${backend}/api/analyze/${session_id}/${act}`

      const progressResponse = await fetch(endpoint)

      if (progressResponse.status === 404) {
        return res.status(404).json({ error: 'Session not found' })
      }

      if (progressResponse.status === 202) {
        const data = await progressResponse.json()
        return res.status(202).json(data)
      }

      if (!progressResponse.ok) {
        const error = await progressResponse.text()
        return res.status(progressResponse.status).json({ error })
      }

      const data = await progressResponse.json()
      return res.status(200).json(data)
    }

    return res.status(405).json({ error: 'Method not allowed' })
  } catch (e: any) {
    console.error('API proxy error:', e)
    return res.status(500).json({ error: e.message })
  }
}
