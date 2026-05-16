import React, { useState } from 'react'
import { SeverityBadge } from './SeverityBadge'

type Issue = { component: string; issue: string; severity?: string; rationale?: string }
type Flow = { from: string; to: string; validation: boolean; risk_level?: string }
type EntryPoint = { path: string; handler: string; auth?: string; risk_level?: string }

export function RiskList({
  entryPoints = [],
  dataFlows = [],
  privilegeIssues = [],
}: {
  entryPoints?: EntryPoint[]
  dataFlows?: Flow[]
  privilegeIssues?: Issue[]
}) {
  return (
    <div className="grid gap-6 xl:grid-cols-2">
      <section className="rounded-3xl border border-white/10 bg-white/[0.03] p-6 shadow-glow backdrop-blur">
        <div className="mb-4 text-xs font-semibold uppercase tracking-[0.3em] text-slate-400">Entry Points</div>
        <div className="overflow-hidden rounded-2xl border border-white/10">
          <table className="w-full border-collapse text-left text-sm">
            <thead className="bg-white/[0.03] text-[10px] uppercase tracking-[0.25em] text-slate-400">
              <tr>
                <th className="px-4 py-3 font-semibold">Path</th>
                <th className="px-4 py-3 font-semibold">Auth</th>
                <th className="px-4 py-3 font-semibold text-right">Risk</th>
              </tr>
            </thead>
            <tbody>
              {entryPoints.map((entry) => (
                <tr key={`${entry.path}-${entry.handler}`} className="border-t border-white/10">
                  <td className="px-4 py-3 font-mono text-xs text-slate-200">{entry.path}</td>
                  <td className="px-4 py-3 font-mono text-xs text-slate-400">{entry.auth || 'unknown'}</td>
                  <td className="px-4 py-3 text-right"><SeverityBadge level={entry.risk_level} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="rounded-3xl border border-white/10 bg-white/[0.03] p-6 shadow-glow backdrop-blur">
        <div className="mb-4 text-xs font-semibold uppercase tracking-[0.3em] text-slate-400">Data Flows</div>
        <div className="space-y-3">
          {dataFlows.map((flow) => (
            <div key={`${flow.from}-${flow.to}`} className="flex items-center justify-between gap-4 rounded-2xl border border-white/10 bg-slate-950/50 p-4">
              <div className="flex items-center gap-2 font-mono text-xs text-slate-300">
                <span>{flow.from}</span>
                <span className="text-slate-500">→</span>
                <span>{flow.to}</span>
              </div>
              <div className="flex items-center gap-3">
                <span className={`text-[10px] font-semibold uppercase tracking-[0.25em] ${flow.validation ? 'text-emerald-300' : 'text-rose-300'}`}>
                  {flow.validation ? 'Validated' : 'Unvalidated'}
                </span>
                <SeverityBadge level={flow.risk_level} />
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="rounded-3xl border border-white/10 bg-white/[0.03] p-6 shadow-glow backdrop-blur xl:col-span-2">
        <div className="mb-4 text-xs font-semibold uppercase tracking-[0.3em] text-slate-400">Privilege Violations</div>
        <div className="space-y-4">
          {privilegeIssues.map((issue) => (
            <PrivilegeIssueItem key={`${issue.component}-${issue.issue}`} issue={issue} />
          ))}
        </div>
      </section>
    </div>
  )
}

function PrivilegeIssueItem({ issue }: { issue: Issue }) {
  const [open, setOpen] = useState(false)

  return (
    <article className="overflow-hidden rounded-2xl border border-white/10 bg-slate-950/55">
      <div className="flex items-start gap-4 p-4">
        <SeverityBadge level={issue.severity} />
        <div className="flex-1">
          <div className="font-mono text-xs text-slate-400">{issue.component}</div>
          <div className="mt-1 text-sm font-medium leading-relaxed text-slate-100">{issue.issue}</div>
        </div>
      </div>
      {issue.rationale && (
        <button type="button" onClick={() => setOpen((value) => !value)} className="w-full border-t border-white/10 px-4 py-3 text-left text-xs uppercase tracking-[0.25em] text-slate-400 hover:bg-white/[0.03]">
          Why this matters {open ? '−' : '+'}
        </button>
      )}
      {open && issue.rationale && <div className="border-t border-white/10 px-4 py-4 text-sm leading-relaxed text-slate-300">{issue.rationale}</div>}
    </article>
  )
}
