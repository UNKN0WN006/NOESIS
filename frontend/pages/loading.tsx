import React, { useEffect, useMemo, useState } from 'react'
import { useRouter } from 'next/router'
import { LogViewer } from '../components/LogViewer'
import { mockLogs } from '../lib/mock-data'

const stages = ['Cloning repository', 'Resolving dependency graph', 'Mapping entry points', 'Tracing data flows', 'Checking privilege boundaries', 'Scoring risk', 'Finalizing report']

export default function LoadingPage() {
  const router = useRouter()
  const [progress, setProgress] = useState(7)
  const [logs, setLogs] = useState(mockLogs)
  const [stageIndex, setStageIndex] = useState(0)

  const repoUrl = useMemo(() => {
    if (typeof window === 'undefined') return ''
    return sessionStorage.getItem('noesis_repo_url') || ''
  }, [])

  useEffect(() => {
    const interval = window.setInterval(() => {
      setProgress((value) => Math.min(value + 11, 100))
      setStageIndex((value) => Math.min(value + 1, stages.length - 1))
      setLogs((value) => [
        ...value,
        {
          ts: new Date().toISOString(),
          level: ['info', 'debug', 'warn'][Math.floor(Math.random() * 3)] as 'info' | 'debug' | 'warn',
          message: stages[Math.min(stageIndex, stages.length - 1)],
        },
      ])
    }, 850)

    return () => window.clearInterval(interval)
  }, [stageIndex])

  useEffect(() => {
    if (progress < 100) return

    const timer = window.setTimeout(async () => {
      const body = JSON.stringify({ repo_url: repoUrl || 'https://github.com/example/vulnerable-app' })
      const response = await fetch('/api/analysis', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body,
      })
      const result = await response.json()
      sessionStorage.setItem('noesis_result', JSON.stringify(result))
      await router.push('/dashboard')
    }, 800)

    return () => window.clearTimeout(timer)
  }, [progress, repoUrl, router])

  return (
    <main className="flex min-h-screen items-center justify-center px-4 py-12">
      <div className="w-full max-w-4xl space-y-8">
        <div className="text-center">
          <div className="mb-4 text-xs font-semibold uppercase tracking-[0.35em] text-cyan-200">Analysis in progress</div>
          <h1 className="text-3xl font-black tracking-tight text-white md:text-4xl">NOESIS is reasoning across the repository context.</h1>
          <p className="mx-auto mt-3 max-w-2xl text-sm leading-relaxed text-slate-400">
            Every stage is designed to look like a real security review: repository structure, data flow, privilege boundaries, and prioritized remediation.
          </p>
        </div>

        <div className="rounded-3xl border border-white/10 bg-white/[0.03] p-6 shadow-glow backdrop-blur">
          <div className="mb-3 flex items-center justify-between text-xs font-semibold uppercase tracking-[0.3em] text-slate-400">
            <span>{stages[Math.min(stageIndex, stages.length - 1)]}</span>
            <span>{Math.min(progress, 100)}%</span>
          </div>
          <div className="h-3 overflow-hidden rounded-full bg-white/5">
            <div className="h-full rounded-full bg-gradient-to-r from-cyan-400 via-blue-400 to-indigo-400 transition-all duration-500" style={{ width: `${Math.min(progress, 100)}%` }} />
          </div>
        </div>

        <div>
          <div className="mb-3 text-xs font-semibold uppercase tracking-[0.3em] text-slate-400">Live execution log</div>
          <LogViewer logs={logs} />
        </div>
      </div>
    </main>
  )
}
