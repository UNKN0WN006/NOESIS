// SeverityBadge: small, consistent badge used across the dashboard.
import React from 'react'

type Severity = 'critical' | 'high' | 'medium' | 'low' | string | null | undefined

export function SeverityBadge({ level }: { level?: Severity }) {
  const value = (level || 'unknown').toString().toLowerCase()
  const classes: Record<string, string> = {
    critical: 'border-rose-500/40 bg-rose-500/10 text-rose-300',
    high: 'border-orange-500/40 bg-orange-500/10 text-orange-300',
    medium: 'border-amber-500/40 bg-amber-500/10 text-amber-300',
    low: 'border-emerald-500/40 bg-emerald-500/10 text-emerald-300',
    unknown: 'border-slate-500/40 bg-slate-500/10 text-slate-300',
  }

  return (
    <span className={`inline-flex items-center rounded-full border px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.2em] ${classes[value] || classes.unknown}`}>
      {value}
    </span>
  )
}
