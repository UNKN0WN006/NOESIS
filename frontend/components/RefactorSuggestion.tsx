import React from 'react'
import { SeverityBadge } from './SeverityBadge'

export function RefactorSuggestion({ suggestion }: { suggestion: any }) {
  return (
    <article className="overflow-hidden rounded-3xl border border-white/10 bg-white/[0.03] shadow-glow backdrop-blur">
      <div className="h-1 bg-gradient-to-r from-cyan-400 via-blue-400 to-indigo-400" />
      <div className="p-6">
        <div className="mb-4 flex items-start justify-between gap-4">
          <div>
            <div className="text-xs font-semibold uppercase tracking-[0.3em] text-slate-400">Remediation Plan</div>
            <h3 className="mt-2 text-sm font-semibold uppercase tracking-[0.2em] text-white">Security refactor</h3>
          </div>
          <div className="flex flex-wrap gap-2">
            <span className="rounded-full border border-white/10 bg-white/[0.04] px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.25em] text-slate-300">
              Effort: {suggestion.effort || 'low'}
            </span>
            <SeverityBadge level={suggestion.severity} />
          </div>
        </div>

        <div className="grid gap-4 lg:grid-cols-2">
          <div className="space-y-4">
            <div>
              <div className="mb-2 text-[10px] font-semibold uppercase tracking-[0.25em] text-slate-500">The vulnerability</div>
              <div className="border-l-2 border-rose-400/60 pl-3 text-sm leading-relaxed text-slate-200">{suggestion.why}</div>
            </div>
            <div>
              <div className="mb-2 text-[10px] font-semibold uppercase tracking-[0.25em] text-slate-500">The fix</div>
              <div className="border-l-2 border-emerald-400/60 pl-3 text-sm leading-relaxed text-slate-200">{suggestion.fix}</div>
            </div>
          </div>

          {suggestion.code_snippet && (
            <pre className="overflow-x-auto rounded-2xl border border-white/10 bg-slate-950/70 p-4 text-xs leading-relaxed text-cyan-200">
              <code>{suggestion.code_snippet}</code>
            </pre>
          )}
        </div>

        {Array.isArray(suggestion.files) && suggestion.files.length > 0 && (
          <div className="mt-4 flex flex-wrap gap-2">
            {suggestion.files.map((file: string) => (
              <span key={file} className="rounded-full border border-white/10 bg-white/[0.04] px-2.5 py-1 text-[11px] text-slate-300">
                {file}
              </span>
            ))}
          </div>
        )}
      </div>
    </article>
  )
}
