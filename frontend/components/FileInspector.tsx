// FileInspector: sortable file risk index with quick severity badges.
import React, { useMemo, useState } from 'react'
import { SeverityBadge } from './SeverityBadge'

export function FileInspector({ files = [] }: { files: any[] }) {
  const [sortAsc, setSortAsc] = useState(false)

  const sorted = useMemo(() => {
    return [...files].sort((left, right) => (sortAsc ? left.risk_score - right.risk_score : right.risk_score - left.risk_score))
  }, [files, sortAsc])

  return (
    <section className="rounded-3xl border border-white/10 bg-white/[0.03] p-6 shadow-glow backdrop-blur">
      <div className="mb-4 flex items-center justify-between gap-4">
        <div className="text-xs font-semibold uppercase tracking-[0.3em] text-slate-400">File Risk Index</div>
        <button
          type="button"
          onClick={() => setSortAsc((value) => !value)}
          className="rounded-full border border-white/10 bg-white/[0.04] px-3 py-2 text-[10px] font-semibold uppercase tracking-[0.25em] text-slate-300"
        >
          Sort {sortAsc ? 'High → Low' : 'Low → High'}
        </button>
      </div>
      <div className="space-y-3">
        {sorted.map((file) => (
          <div key={file.path} className="flex flex-col justify-between gap-4 rounded-2xl border border-white/10 bg-slate-950/55 p-4 sm:flex-row sm:items-center">
            <div className="flex items-start gap-4">
              <div className={`w-14 shrink-0 text-center text-2xl font-black ${file.risk_score >= 80 ? 'text-rose-300' : file.risk_score >= 60 ? 'text-orange-300' : 'text-amber-300'}`}>
                {file.risk_score}
              </div>
              <div>
                <div className="font-mono text-sm font-semibold text-white">{file.path}</div>
                <div className="mt-2 flex flex-wrap gap-2">
                  {file.issues.map((issue: string) => (
                    <span key={issue} className="rounded-full border border-white/10 bg-white/[0.04] px-2.5 py-1 text-xs text-slate-300">
                      {issue}
                    </span>
                  ))}
                </div>
              </div>
            </div>
            <SeverityBadge level={file.severity} />
          </div>
        ))}
      </div>
    </section>
  )
}
