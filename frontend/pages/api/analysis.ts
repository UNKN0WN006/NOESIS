import type { NextApiRequest, NextApiResponse } from 'next'

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'POST') return res.status(405).end()
  const body = req.body
  try {
    const backend = process.env.BACKEND_URL || 'http://localhost:8000'
    const r = await fetch(`${backend}/analyze`, {method: 'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body)})
    const data = await r.json()
    res.status(200).json(data)
  } catch (e:any){
    res.status(500).json({error: e.message})
  }
}
