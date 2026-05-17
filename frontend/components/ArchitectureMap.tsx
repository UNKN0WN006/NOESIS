// ArchitectureMap: visual list of architectural components and affected files.
import React from 'react'
import { SeverityBadge } from './SeverityBadge'

type Node = {
  name: string
  files: string[]
  desc: string
  risk_level?: string | null
}

const chipTone: Record<string, string> = {
  critical: 'bg-rose-500/10 text-rose-300 border-rose-500/20',
  high: 'bg-orange-500/10 text-orange-300 border-orange-500/20',
  medium: 'bg-amber-500/10 text-amber-300 border-amber-500/20',
  low: 'bg-emerald-500/10 text-emerald-300 border-emerald-500/20',
}

export function ArchitectureMap({ nodes }: { nodes: Node[] }) {
  return (
    <div className="rounded-3xl border border-white/10 bg-white/[0.03] p-6 shadow-glow backdrop-blur">
      <div className="mb-5 text-xs font-semibold uppercase tracking-[0.3em] text-slate-400">Architecture Topology</div>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {nodes.map((node) => {
          const key = (node.risk_level || 'low').toLowerCase()
          return (
            <article key={node.name} className="rounded-2xl border border-white/10 bg-slate-950/60 p-4">
              <div className="mb-3 flex items-start justify-between gap-3">
                <div>
                  <div className="text-sm font-semibold capitalize text-white">{node.name}</div>
                  <div className="mt-1 text-xs text-slate-400">{node.desc}</div>
                </div>
                <SeverityBadge level={node.risk_level} />
              </div>
              <div className={`mb-3 inline-flex rounded-full border px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.25em] ${chipTone[key] || chipTone.low}`}>
                {node.name}
              </div>
              <div className="space-y-2">
                <div className="text-[10px] font-semibold uppercase tracking-[0.25em] text-slate-500">Files affected</div>
                <div className="flex flex-wrap gap-2">
                  {node.files.map((file) => (
                    <span key={file} className="rounded-full border border-white/10 bg-white/[0.04] px-2.5 py-1 text-[11px] text-slate-300">
                      {file}
                    </span>
                  ))}
                </div>
              </div>
            </article>
          )
        })}
      </div>
    </div>
  )
}
