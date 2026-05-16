import React, { useState } from 'react'
import { useRouter } from 'next/router'
import { mockAnalysisResult } from '../lib/mock-data'

export default function Home() {
  const router = useRouter()
  const [repo, setRepo] = useState('')
  const [error, setError] = useState('')

  async function submit(event: React.FormEvent) {
    event.preventDefault()

    if (!repo.trim()) {
      setError('Repository URL is required')
      return
    }

    try {
      new URL(repo)
    } catch {
      setError('Enter a valid repository URL')
      return
    }

    setError('')
    sessionStorage.setItem('noesis_repo_url', repo)
    sessionStorage.setItem('noesis_preview', JSON.stringify(mockAnalysisResult))
    await router.push('/loading')
  }

  return (
    <main className="flex min-h-screen items-center justify-center px-4 py-12">
      <div className="w-full max-w-2xl rounded-[2rem] border border-white/10 bg-white/[0.03] p-8 shadow-glow backdrop-blur md:p-10">
        <div className="mb-10 text-center">
          <div className="mb-4 inline-flex rounded-full border border-cyan-400/20 bg-cyan-400/10 px-4 py-2 text-[11px] font-semibold uppercase tracking-[0.35em] text-cyan-200">
            NOESIS / Nested Orchestration of Exploitability & Structure Insight System
          </div>
          <h1 className="text-4xl font-black tracking-tight text-white md:text-5xl">Repository security, rendered as architecture intelligence.</h1>
          <p className="mx-auto mt-4 max-w-xl text-sm leading-relaxed text-slate-400">
            Feed NOESIS a repository URL and it will stage an analyst-style review of exposure, data flow, privilege boundaries, and refactor risk.
          </p>
        </div>

        <form onSubmit={submit} className="space-y-4">
          <div>
            <label className="mb-2 block text-xs font-semibold uppercase tracking-[0.3em] text-slate-400">Repository URL</label>
            <input
              type="text"
              value={repo}
              onChange={(event) => setRepo(event.target.value)}
              placeholder="https://github.com/organization/repository"
              className="w-full rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 font-mono text-sm text-white outline-none transition placeholder:text-slate-600 focus:border-cyan-400/40"
            />
            {error && <p className="mt-2 text-xs font-mono text-rose-300">{error}</p>}
          </div>

          <button
            type="submit"
            className="inline-flex w-full items-center justify-center rounded-2xl bg-white px-4 py-3 text-sm font-semibold uppercase tracking-[0.25em] text-slate-950 transition hover:bg-cyan-200"
          >
            Start Analysis
          </button>
        </form>

        <div className="mt-10 grid gap-4 md:grid-cols-3">
          {[
            ['Attack surface', 'Entry points, auth gaps, exposure paths'],
            ['Data flow', 'How input reaches storage and sinks'],
            ['Remediation', 'Priority fixes with concise rationale'],
          ].map(([title, body]) => (
            <div key={title} className="rounded-2xl border border-white/10 bg-slate-950/55 p-4">
              <div className="text-xs font-semibold uppercase tracking-[0.25em] text-slate-400">{title}</div>
              <div className="mt-2 text-sm leading-relaxed text-slate-300">{body}</div>
            </div>
          ))}
        </div>
      </div>
    </main>
  )
}

