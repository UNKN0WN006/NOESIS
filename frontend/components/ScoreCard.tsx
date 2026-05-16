import React from 'react'

export function ScoreCard({ score }: { score: number }) {
  const label = score >= 80 ? 'Critical risk detected' : score >= 60 ? 'High risk detected' : score >= 40 ? 'Elevated risk detected' : 'Acceptable risk level'
  const color = score >= 80 ? 'text-rose-300' : score >= 60 ? 'text-orange-300' : score >= 40 ? 'text-amber-300' : 'text-emerald-300'

  return (
    <div className="rounded-3xl border border-white/10 bg-white/[0.03] p-8 shadow-glow backdrop-blur">
      <div className="mb-2 text-xs font-semibold uppercase tracking-[0.3em] text-slate-400">Exploitability Score</div>
      <div className={`text-7xl font-black tracking-tight ${color}`}>{score}</div>
      <div className="mt-4 text-xs font-mono uppercase tracking-[0.25em] text-slate-500">{label}</div>
    </div>
  )
}

