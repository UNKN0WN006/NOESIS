// Dashboard page: renders final analysis report and drill-down components.
import React, { useEffect, useMemo, useState } from 'react'
import { useRouter } from 'next/router'
import { ArchitectureMap } from '../components/ArchitectureMap'
import { FileInspector } from '../components/FileInspector'
import { Heatmap } from '../components/Heatmap'
import { RefactorSuggestion } from '../components/RefactorSuggestion'
import { RiskList } from '../components/RiskList'
import { ScoreCard } from '../components/ScoreCard'
import { sampleAnalysisResult } from '../lib/sample-data'

export default function Dashboard() {
  const router = useRouter()
  const [result, setResult] = useState<any>(sampleAnalysisResult)

  const repoUrl = useMemo(() => {
    if (typeof window === 'undefined') return sampleAnalysisResult.repo_url
    return sessionStorage.getItem('noesis_repo_url') || sampleAnalysisResult.repo_url
  }, [])

  useEffect(() => {
    if (typeof window === 'undefined') return
    const raw = sessionStorage.getItem('noesis_result')
    if (raw) {
      setResult(JSON.parse(raw))
    }
  }, [])

  return (
    <main className="min-h-screen px-4 py-6 md:px-6">
      <header className="sticky top-4 z-10 mx-auto mb-8 max-w-[1600px] rounded-3xl border border-white/10 bg-slate-950/80 px-5 py-4 shadow-glow backdrop-blur">
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div>
            <div className="text-xs font-semibold uppercase tracking-[0.35em] text-cyan-200">NOESIS // REPORT</div>
            <h1 className="mt-1 text-lg font-bold tracking-tight text-white">Repository Risk Intelligence Dashboard</h1>
          </div>
          <div className="rounded-2xl border border-white/10 bg-white/[0.04] px-4 py-2 font-mono text-xs text-slate-300">
            Target: {repoUrl}
          </div>
        </div>
      </header>

      <section className="mx-auto max-w-[1600px] space-y-6">
        <div className="grid gap-6 lg:grid-cols-3">
          <ScoreCard score={result.score} />
          <div className="lg:col-span-2">
            <Heatmap breakdown={result.score_breakdown} />
          </div>
        </div>

        <ArchitectureMap nodes={result.architecture} />

        <RiskList entryPoints={result.entry_points} dataFlows={result.data_flows} privilegeIssues={result.privilege_issues} />

        <section className="space-y-4">
          <div className="text-xs font-semibold uppercase tracking-[0.3em] text-slate-400">Refactor intelligence</div>
          <div className="space-y-4">
            {result.suggestions.map((suggestion: any, index: number) => (
              <RefactorSuggestion key={`${suggestion.why}-${index}`} suggestion={suggestion} />
            ))}
          </div>
        </section>

        <FileInspector files={result.file_risks} />

        <div className="flex justify-end pb-6">
          <button
            type="button"
            onClick={() => router.push('/')}
            className="rounded-2xl border border-white/10 bg-white/[0.04] px-4 py-3 text-xs font-semibold uppercase tracking-[0.25em] text-slate-300"
          >
            Analyze another repository
          </button>
        </div>
      </section>
    </main>
  )
}

