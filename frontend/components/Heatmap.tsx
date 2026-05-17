// Heatmap: simple, accessible horizontal bars to show per-factor risk.
import React from 'react'

function formatLabel(key: string) {
  return key
    .split('_')
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ')
}

export function Heatmap({ breakdown }: { breakdown?: Record<string, unknown> | null }) {
  if (!breakdown) return null

  const data = Object.entries(breakdown)
    .map(([key, value]) => ({ label: formatLabel(key), score: Number(value) || 0 }))
    .sort((left, right) => right.score - left.score)

  const tone = (score: number) => {
    if (score >= 80) return 'from-rose-500 to-rose-300'
    if (score >= 60) return 'from-orange-500 to-orange-300'
    if (score >= 40) return 'from-amber-500 to-amber-300'
    return 'from-emerald-500 to-emerald-300'
  }

  return (
    <div className="rounded-3xl border border-white/10 bg-white/[0.03] p-6 shadow-glow backdrop-blur">
      <div className="mb-5 text-xs font-semibold uppercase tracking-[0.3em] text-slate-400">Risk Breakdown</div>
      <div className="space-y-4">
        {data.map((entry) => (
          <div key={entry.label} className="space-y-2">
            <div className="flex items-center justify-between text-xs font-mono text-slate-400">
              <span>{entry.label}</span>
              <span>{entry.score}</span>
            </div>
            <div className="h-3 overflow-hidden rounded-full bg-white/5">
              <div className={`h-full rounded-full bg-gradient-to-r ${tone(entry.score)}`} style={{ width: `${Math.min(entry.score, 100)}%` }} />
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

