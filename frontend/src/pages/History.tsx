import { useQuery } from '@tanstack/react-query'
import { historyApi } from '@/lib/api'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import { History as HistoryIcon, Activity, CheckCircle2, XCircle, Clock, Bot } from 'lucide-react'
import { statusConfig, timeAgo, cn } from '@/lib/utils'
import type { Application, AgentLog } from '@/types'

const LEVEL_COLOR: Record<string, string> = {
  info:    'text-blue-400 bg-blue-500/10 border-blue-500/20',
  warning: 'text-amber-400 bg-amber-500/10 border-amber-500/20',
  error:   'text-red-400 bg-red-500/10 border-red-500/20',
}

const AGENT_COLOR: Record<string, string> = {
  SupervisorAgent:    'bg-violet-500/10 text-violet-400 border-violet-500/20',
  SourcingAgent:      'bg-sky-500/10 text-sky-400 border-sky-500/20',
  JobAnalysisAgent:   'bg-amber-500/10 text-amber-400 border-amber-500/20',
  ResumeTailorAgent:  'bg-pink-500/10 text-pink-400 border-pink-500/20',
  ApplicationAgent:   'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  MemoryAgent:        'bg-cyan-500/10 text-cyan-400 border-cyan-500/20',
  AuditAgent:         'bg-slate-500/10 text-slate-400 border-slate-500/20',
}

export function History() {
  const { data: apps = [], isLoading: appsLoading } = useQuery<Application[]>({
    queryKey: ['history-apps'],
    queryFn: () => historyApi.applications(200),
    refetchInterval: 15_000,
  })

  const { data: logs = [], isLoading: logsLoading } = useQuery<AgentLog[]>({
    queryKey: ['history-logs'],
    queryFn: () => historyApi.logs(500),
    refetchInterval: 10_000,
  })

  const successCount = apps.filter(a => a.result === 'success').length
  const failedCount  = apps.filter(a => a.result === 'failed').length
  const pendingCount = apps.filter(a => a.result === 'pending').length

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold gradient-text">History</h1>
        <p className="text-sm text-muted-foreground mt-0.5">Full audit trail — agent decisions, applications, and outcomes</p>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <Card><CardContent className="p-4 flex items-center gap-3">
          <CheckCircle2 className="h-5 w-5 text-emerald-400 shrink-0" />
          <div><p className="text-xl font-bold text-emerald-400">{successCount}</p><p className="text-xs text-muted-foreground">Successful</p></div>
        </CardContent></Card>
        <Card><CardContent className="p-4 flex items-center gap-3">
          <XCircle className="h-5 w-5 text-red-400 shrink-0" />
          <div><p className="text-xl font-bold text-red-400">{failedCount}</p><p className="text-xs text-muted-foreground">Failed</p></div>
        </CardContent></Card>
        <Card><CardContent className="p-4 flex items-center gap-3">
          <Clock className="h-5 w-5 text-amber-400 shrink-0" />
          <div><p className="text-xl font-bold text-amber-400">{pendingCount}</p><p className="text-xs text-muted-foreground">Pending</p></div>
        </CardContent></Card>
      </div>

      <Tabs defaultValue="logs">
        <TabsList>
          <TabsTrigger value="logs" className="gap-2"><Activity className="h-3.5 w-3.5" />Agent Logs</TabsTrigger>
          <TabsTrigger value="applications" className="gap-2"><HistoryIcon className="h-3.5 w-3.5" />Applications</TabsTrigger>
        </TabsList>

        <TabsContent value="logs">
          {logsLoading ? (
            <div className="space-y-2">{[...Array(8)].map((_, i) => <div key={i} className="h-14 skeleton rounded-xl" />)}</div>
          ) : (
            <Card>
              <CardContent className="p-0">
                <div className="divide-y divide-border max-h-[65vh] overflow-auto">
                  {logs.map(log => (
                    <div key={log.id} className="flex items-start gap-3 p-3 hover:bg-secondary/30 transition-colors">
                      {/* Level */}
                      <span className={cn('inline-flex items-center rounded-full border px-2 py-0.5 text-[10px] font-semibold shrink-0 mt-0.5', LEVEL_COLOR[log.level] ?? 'text-muted-foreground bg-muted border-border')}>
                        {log.level.toUpperCase()}
                      </span>

                      {/* Agent chip */}
                      {log.agent_name && (
                        <span className={cn('inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[10px] font-medium shrink-0 mt-0.5', AGENT_COLOR[log.agent_name] ?? 'bg-muted text-muted-foreground border-border')}>
                          <Bot className="h-2.5 w-2.5" />{log.agent_name.replace('Agent', '')}
                        </span>
                      )}

                      {/* Content */}
                      <div className="flex-1 min-w-0">
                        <span className="text-xs font-semibold text-primary">{log.event}</span>
                        {log.message && <span className="text-xs text-muted-foreground ml-2">{log.message}</span>}
                        {log.decision_reason && (
                          <p className="text-[10px] text-muted-foreground/70 mt-0.5 italic">{log.decision_reason}</p>
                        )}
                      </div>

                      {/* Decision + time */}
                      <div className="flex flex-col items-end gap-1 shrink-0">
                        {log.decision && (
                          <span className={cn('text-[9px] font-bold uppercase tracking-wide',
                            log.decision === 'proceed' ? 'text-emerald-400' :
                            log.decision === 'await_approval' ? 'text-amber-400' :
                            log.decision === 'fail' ? 'text-red-400' : 'text-muted-foreground'
                          )}>{log.decision}</span>
                        )}
                        <span className="text-[10px] text-muted-foreground">{timeAgo(log.created_at)}</span>
                      </div>
                    </div>
                  ))}
                  {logs.length === 0 && (
                    <p className="text-sm text-muted-foreground text-center py-8">No agent logs yet</p>
                  )}
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="applications">
          {appsLoading ? (
            <div className="space-y-3">{[...Array(5)].map((_, i) => <div key={i} className="h-16 skeleton rounded-xl" />)}</div>
          ) : apps.length === 0 ? (
            <Card><CardContent className="py-12 text-center text-muted-foreground">No applications yet</CardContent></Card>
          ) : (
            <div className="space-y-2">
              {apps.map(app => {
                const sc = statusConfig(app.status)
                return (
                  <Card key={app.id} className="hover:border-primary/20 transition-colors">
                    <CardContent className="p-4 flex items-center gap-4">
                      <div className={cn('h-8 w-8 rounded-full flex items-center justify-center shrink-0',
                        app.result === 'success' ? 'bg-emerald-500/10' :
                        app.result === 'failed'  ? 'bg-red-500/10' : 'bg-amber-500/10'
                      )}>
                        {app.result === 'success' ? <CheckCircle2 className="h-4 w-4 text-emerald-400" /> :
                         app.result === 'failed'  ? <XCircle      className="h-4 w-4 text-red-400" /> :
                                                    <Clock         className="h-4 w-4 text-amber-400" />}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium">Application #{app.id.slice(-8)}</p>
                        <p className="text-xs text-muted-foreground">Job: {app.job_id.slice(-12)} · {timeAgo(app.created_at)}</p>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className={cn('inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium', sc.color)}>{sc.label}</span>
                        {app.confirmation_number && (
                          <span className="text-xs font-mono text-muted-foreground">#{app.confirmation_number.slice(-8)}</span>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                )
              })}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  )
}
