// API proxy: forwards analysis requests from Next.js to the FastAPI backend.
import type { NextApiRequest, NextApiResponse } from 'next'
import sampleData from '../../lib/sample-data'

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  const backend = process.env.BACKEND_URL || null
  
  // helper: fetch with AbortController timeout
  const fetchWithTimeout = async (url: string, opts: any = {}, timeout = 5000) => {
    const controller = new AbortController()
    const id = setTimeout(() => controller.abort(), timeout)
    try {
      const r = await fetch(url, { signal: controller.signal, ...opts })
      clearTimeout(id)
      return r
    } catch (e) {
      clearTimeout(id)
      throw e
    }
  }
  
  try {
    if (req.method === 'POST') {
      const { repo_url } = req.body
      if (!repo_url) {
        return res.status(400).json({ error: 'repo_url is required' })
      }

      // If no backend configured, return a demo completed session using sample data
      if (!backend) {
        return res.status(200).json({ session_id: 'sample', status: 'completed', result: sampleData })
      }

      try {
        const initResponse = await fetchWithTimeout(`${backend}/api/analyze`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ repo_url }),
        }, 7000)

        if (!initResponse.ok) {
          const error = await initResponse.text()
          return res.status(initResponse.status).json({ error })
        }

        const data = await initResponse.json()
        return res.status(200).json(data)
      } catch (e: any) {
        console.warn('Backend POST failed, falling back to sample:', e?.message)
        return res.status(200).json({ session_id: 'sample', status: 'completed', result: sampleData })
      }
    }

    if (req.method === 'GET') {
      const { session_id, action } = req.query

      if (!session_id || typeof session_id !== 'string') {
        return res.status(400).json({ error: 'session_id query parameter required' })
      }

      const act = action === 'result' ? 'result' : 'progress'
      
      // fallback to sample results when backend is not configured or session is 'sample'
      if (!backend || session_id === 'sample') {
        if (act === 'progress') {
          return res.status(202).json({ session_id: 'sample', status: 'completed', progress: 100 })
        }
        return res.status(200).json({ session_id: 'sample', status: 'completed', result: sampleData })
      }

      try {
        const endpoint = `${backend}/api/analyze/${session_id}/${act}`

        const progressResponse = await fetchWithTimeout(endpoint, {}, 7000)

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
      } catch (e: any) {
        console.warn('Backend GET failed, falling back to sample:', e?.message)
        if (act === 'progress') {
          return res.status(202).json({ session_id: 'sample', status: 'completed', progress: 100 })
        }
        return res.status(200).json({ session_id: 'sample', status: 'completed', result: sampleData })
      }
    }

    return res.status(405).json({ error: 'Method not allowed' })
  } catch (e: any) {
    console.error('API proxy error:', e)
    return res.status(500).json({ error: e.message })
  }
}
