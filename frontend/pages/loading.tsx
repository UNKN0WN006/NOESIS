// Loading page: starts analysis, polls progress, and redirects on completion.
import React, { useEffect, useState } from 'react'
import { useRouter } from 'next/router'
import { LogViewer } from '../components/LogViewer'

interface LogLine {
  timestamp: string
  level: 'info' | 'debug' | 'warn' | 'error'
  message: string
}

export default function LoadingPage() {
  const router = useRouter()
  const [progress, setProgress] = useState(0)
  const [logs, setLogs] = useState<LogLine[]>([])
  const [stage, setStage] = useState('Initializing analysis...')
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const repoUrl = typeof window !== 'undefined' ? sessionStorage.getItem('noesis_repo_url') : null

  useEffect(() => {
    if (!repoUrl || sessionId) return

    const initiate = async () => {
      try {
        const response = await fetch('/api/analysis', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ repo_url: repoUrl }),
        })

        if (!response.ok) {
          const err = await response.text()
          throw new Error(err || 'Failed to initiate analysis')
        }

        const data = await response.json()
        setSessionId(data.session_id)
        setLogs([
          {
            timestamp: new Date().toISOString(),
            level: 'info',
            message: `Analysis started for ${repoUrl}`,
          },
        ])
      } catch (e: any) {
        setError(e.message)
      }
    }

    initiate()
  }, [repoUrl, sessionId])

  useEffect(() => {
    if (!sessionId || progress >= 100) return

    const interval = setInterval(async () => {
      try {
        const response = await fetch(`/api/analysis?session_id=${sessionId}&action=progress`)

        if (response.status === 404) {
          setError('Session not found')
          return
        }

        if (!response.ok) {
          const err = await response.text()
          throw new Error(err)
        }

        const data = await response.json()
        setProgress(data.progress)
        setStage(data.stage || 'Processing...')

        if (data.log_lines && Array.isArray(data.log_lines)) {
          setLogs(
            data.log_lines.map((log: any) => ({
              timestamp: log.timestamp,
              level: log.level,
              message: log.message,
            }))
          )
        }
      } catch (e: any) {
        console.error('Progress poll error:', e)
      }
    }, 750)

    return () => clearInterval(interval)
  }, [sessionId, progress])

  useEffect(() => {
    if (progress < 100 || !sessionId) return

    const timer = setTimeout(async () => {
      try {
        const response = await fetch(`/api/analysis?session_id=${sessionId}&action=result`)

        if (response.status === 202) {
          return
        }

        if (!response.ok) {
          const err = await response.text()
          throw new Error(err)
        }

        const result = await response.json()
        sessionStorage.setItem('noesis_result', JSON.stringify(result))
        sessionStorage.setItem('noesis_session_id', sessionId)

        await router.push('/dashboard')
      } catch (e: any) {
        setError(`Failed to retrieve results: ${e.message}`)
      }
    }, 500)

    return () => clearTimeout(timer)
  }, [progress, sessionId, router])

  if (error) {
    return (
      <div className="min-h-screen bg-slate-950 text-white flex items-center justify-center p-4">
        <div className="max-w-2xl">
          <h1 className="text-4xl font-mono font-bold mb-4 text-rose-500">Error</h1>
          <p className="text-lg mb-6">{error}</p>
          <button
            onClick={() => router.push('/')}
            className="px-6 py-2 bg-blue-600 hover:bg-blue-700 rounded font-mono text-sm"
          >
            Back to Start
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950 text-white p-6">
      <div className="max-w-4xl mx-auto">
        <div className="mb-12">
          <h1 className="text-5xl font-mono font-bold mb-2 bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">
            NOESIS
          </h1>
          <p className="text-slate-400 font-mono">Analyzing repository security architecture...</p>
        </div>

        <div className="mb-8">
          <div className="flex justify-between items-center mb-3">
            <span className="text-sm font-mono text-slate-300">{stage}</span>
            <span className="text-sm font-mono font-bold text-cyan-400">{progress}%</span>
          </div>

          <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden border border-slate-700">
            <div
              className="h-full bg-gradient-to-r from-cyan-400 via-blue-500 to-indigo-600 rounded-full transition-all duration-300 ease-out shadow-lg shadow-cyan-400/50"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        <div className="grid grid-cols-3 gap-4 mb-8">
          <div className="bg-slate-800/50 border border-slate-700 rounded p-4">
            <div className="text-xs text-slate-400 font-mono mb-1">Status</div>
            <div className="text-lg font-mono font-bold text-cyan-400">
              {progress === 100 ? 'Complete' : 'Running'}
            </div>
          </div>
          <div className="bg-slate-800/50 border border-slate-700 rounded p-4">
            <div className="text-xs text-slate-400 font-mono mb-1">Stage</div>
            <div className="text-sm font-mono font-bold text-blue-400 truncate">{stage}</div>
          </div>
          <div className="bg-slate-800/50 border border-slate-700 rounded p-4">
            <div className="text-xs text-slate-400 font-mono mb-1">Progress</div>
            <div className="text-lg font-mono font-bold text-indigo-400">{progress}%</div>
          </div>
        </div>

        <div className="bg-slate-800/30 border border-slate-700 rounded-lg p-4">
          <h2 className="text-sm font-mono font-bold text-slate-300 mb-3 uppercase tracking-wider">
            Execution Log
          </h2>
          <LogViewer
            logs={logs.map((log) => ({
              ts: log.timestamp,
              level: log.level as 'info' | 'debug' | 'warn',
              message: log.message,
            }))}
          />
        </div>

        {progress === 100 && (
          <div className="mt-8 text-center text-sm text-slate-400 font-mono">
            Analysis complete. Preparing dashboard...
          </div>
        )}
      </div>
    </div>
  )
}

