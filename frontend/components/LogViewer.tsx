import React, { useEffect, useRef } from 'react'

export interface LogLine {
  ts: string
  level: 'info' | 'warn' | 'error' | 'debug' | string
  message: string
}

export function LogViewer({ logs }: { logs: LogLine[] }) {
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (ref.current) {
      ref.current.scrollTop = ref.current.scrollHeight
    }
  }, [logs])

  const color = (level: string) => {
    const key = level.toLowerCase()
    if (key === 'error') return 'text-rose-300'
    if (key === 'warn') return 'text-amber-300'
    if (key === 'debug') return 'text-slate-400'
    return 'text-slate-100'
  }

  return (
    <div ref={ref} className="max-h-[360px] overflow-y-auto rounded-2xl border border-white/10 bg-slate-950/70 p-4 font-mono text-[11px] shadow-glow">
      {logs.length === 0 ? (
        <div className="text-slate-500">Waiting for logs...</div>
      ) : (
        logs.map((log, index) => (
          <div key={`${log.ts}-${index}`} className="mb-2 flex gap-3 rounded-lg px-2 py-1 hover:bg-white/5">
            <span className="w-24 shrink-0 text-slate-500">{new Date(log.ts).toISOString().slice(11, 23)}</span>
            <span className={`w-16 shrink-0 font-semibold uppercase ${color(log.level)}`}>[{log.level}]</span>
            <span className={color(log.level)}>{log.message}</span>
          </div>
        ))
      )}
    </div>
  )
}
