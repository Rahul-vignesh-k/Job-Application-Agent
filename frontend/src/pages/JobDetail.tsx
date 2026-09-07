import { useParams, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  ArrowLeft, MapPin, Building2, DollarSign, ExternalLink,
  Zap, Scissors, CheckCircle2, Clock, AlertTriangle, Banknote,
} from 'lucide-react'
import { jobsApi, settingsApi, historyApi } from '@/lib/api'
import { Bot } from 'lucide-react'
import type { AppSettings, AgentLog } from '@/types'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import { ScoreRing } from '@/components/ScoreRing'
import { useToast } from '@/hooks/use-toast'
import { formatSalary, statusConfig, cn, timeAgo } from '@/lib/utils'
import type { Job } from '@/types'

export function JobDetail() {
  const { id } = useParams<{ id: string }>()
  const qc = useQueryClient()
  const { toast } = useToast()

  const { data: job, isLoading } = useQuery<Job>({
    queryKey: ['job', id],
    queryFn: () => jobsApi.get(id!),
    enabled: !!id,
    refetchInterval: 5_000,
  })

  const { data: pendingFields = [] } = useQuery({
    queryKey: ['pending-fields', id],
    queryFn: () => jobsApi.pendingFields(id!),
    enabled: !!id,
  })

  const { data: appSettings } = useQuery<AppSettings>({ queryKey: ['settings'], queryFn: settingsApi.get })

  const { data: jobLogs = [] } = useQuery<AgentLog[]>({
    queryKey: ['job-logs', id],
    queryFn: async () => {
      const all = await historyApi.logs(500)
      return all.filter((l: AgentLog) => l.job_id === id)
    },
    enabled: !!id,
    refetchInterval: 8_000,
  })

  const analyseMut = useMutation({
    mutationFn: () => jobsApi.analyse(id!),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['job', id] }); toast({ title: 'Analysis complete' }) },
    onError: (e: Error) => toast({ title: 'Failed', description: e.message, variant: 'destructive' }),
  })

  const tailorMut = useMutation({
    mutationFn: () => jobsApi.tailor(id!),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['job', id] }); toast({ title: 'Tailored resume generated' }) },
    onError: (e: Error) => toast({ title: 'Failed', description: e.message, variant: 'destructive' }),
  })

  const applyMut = useMutation({
    mutationFn: () => jobsApi.apply(id!),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['job', id] }); toast({ title: 'Application submitted!' }) },
    onError: (e: Error) => toast({ title: 'Apply failed', description: e.message, variant: 'destructive' }),
  })

  const AGENT_COLOR: Record<string, string> = {
    ScraperAgent:   'bg-sky-500/10 text-sky-400 border-sky-500/30',
    AnalysisAgent:  'bg-violet-500/10 text-violet-400 border-violet-500/30',
    TailorAgent:    'bg-amber-500/10 text-amber-400 border-amber-500/30',
    ApplyAgent:     'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
    OrchestratorAgent: 'bg-pink-500/10 text-pink-400 border-pink-500/30',
  }

  if (isLoading) return <div className="space-y-4">{[...Array(3)].map((_, i) => <div key={i} className="h-32 skeleton rounded-xl" />)}</div>
  if (!job) return <div className="text-center py-20 text-muted-foreground">Job not found</div>

  const sc = statusConfig(job.status)
  const md = job.match_details

  return (
    <div className="space-y-6 animate-fade-in max-w-4xl">
      {/* Back */}
      <Link to="/jobs">
        <Button variant="ghost" size="sm" className="gap-1.5 -ml-2 text-muted-foreground hover:text-foreground">
          <ArrowLeft className="h-3.5 w-3.5" /> Back to Queue
        </Button>
      </Link>

      {/* Header card */}
      <Card className="border-primary/20 overflow-hidden">
        <div className="h-1 bg-gradient-to-r from-primary via-primary/60 to-transparent" />
        <CardContent className="p-6">
          <div className="flex items-start gap-5">
            <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-primary/20 to-primary/5 ring-1 ring-primary/20 text-primary font-bold text-xl">
              {job.company.charAt(0)}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-start justify-between gap-4 flex-wrap">
                <div>
                  <h1 className="text-xl font-bold text-foreground">{job.title}</h1>
                  <div className="flex items-center flex-wrap gap-3 text-sm text-muted-foreground mt-1">
                    <span className="flex items-center gap-1"><Building2 className="h-3.5 w-3.5" />{job.company}</span>
                    {job.location && <span className="flex items-center gap-1"><MapPin className="h-3.5 w-3.5" />{job.location}</span>}
                    {(job.salary_min || job.salary_max) && (
                      <span className="flex items-center gap-1">
                        <DollarSign className="h-3.5 w-3.5" />
                        {formatSalary(job.salary_min, job.salary_max, job.salary_currency)}
                      </span>
                    )}
                  </div>
                </div>
                {job.match_score !== undefined && job.match_score !== null && (
                  <ScoreRing score={job.match_score} size={72} />
                )}
              </div>
              <div className="flex items-center gap-2 mt-3 flex-wrap">
                <span className={cn('inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-medium', sc.color)}>
                  <span className={cn('h-1.5 w-1.5 rounded-full', sc.dot)} />{sc.label}
                </span>
                {job.job_classification && (
                  <span className={cn(
                    'inline-flex items-center rounded-full border px-3 py-1 text-xs font-semibold',
                    job.job_classification === 'Internship'
                      ? 'border-violet-500/30 bg-violet-500/10 text-violet-400'
                      : 'border-sky-500/30 bg-sky-500/10 text-sky-400'
                  )}>
                    {job.job_classification}
                  </span>
                )}
                {job.remote_type && <Badge variant="secondary" className="capitalize">{job.remote_type}</Badge>}
                {job.is_easy_apply && <Badge variant="info"><Zap className="h-3 w-3 mr-1" />Easy Apply</Badge>}
                <Badge variant="secondary" className="capitalize">{job.platform}</Badge>
              </div>
            </div>
          </div>

          {/* Action row */}
          <div className="flex flex-wrap gap-2 mt-5 pt-5 border-t border-border/50">
            {job.status === 'discovered' && (
              <Button onClick={() => analyseMut.mutate()} disabled={analyseMut.isPending} variant="glow" size="sm">
                {analyseMut.isPending ? 'Analysing…' : <><Zap className="h-3.5 w-3.5 mr-1.5" />Analyse Match</>}
              </Button>
            )}
            {job.status === 'review_required' && (
              <>
                <Button onClick={() => tailorMut.mutate()} disabled={tailorMut.isPending} size="sm" className="gap-1.5">
                  {tailorMut.isPending ? 'Tailoring…' : <><Scissors className="h-3.5 w-3.5" />Tailor Resume</>}
                </Button>
                <Button onClick={() => applyMut.mutate()} disabled={applyMut.isPending} variant="outline" size="sm">
                  Apply with Base Resume
                </Button>
              </>
            )}
            {job.status === 'ready_to_apply' && (
              <Button onClick={() => applyMut.mutate()} disabled={applyMut.isPending} variant="success" size="sm">
                {applyMut.isPending ? 'Applying…' : <><CheckCircle2 className="h-3.5 w-3.5 mr-1.5" />Apply Now</>}
              </Button>
            )}
            {job.apply_url && (
              <Button variant="outline" size="sm" asChild>
                <a href={job.apply_url} target="_blank" rel="noopener noreferrer">
                  <ExternalLink className="h-3.5 w-3.5 mr-1.5" />Open Job
                </a>
              </Button>
            )}
          </div>

          {/* Salary to be used */}
          {job.job_classification && appSettings && (
            <div className="mt-3 flex items-center gap-2 text-xs text-muted-foreground">
              <Banknote className="h-3.5 w-3.5 shrink-0" />
              <span>
                Salary to be submitted:{' '}
                <span className="font-semibold text-foreground">
                  {job.job_classification === 'Internship'
                    ? appSettings.user_expected_salary_intern || '—'
                    : appSettings.user_expected_salary_fte || '—'}
                </span>
                {' '}({job.job_classification})
              </span>
            </div>
          )}

          {/* Waiting input notice */}
          {job.status === 'waiting_input' && pendingFields.length > 0 && (
            <div className="mt-4 rounded-lg border border-orange-500/30 bg-orange-500/10 p-3">
              <p className="text-sm text-orange-300 font-medium flex items-center gap-2">
                <AlertTriangle className="h-4 w-4" />
                {pendingFields.length} form field{pendingFields.length > 1 ? 's' : ''} need your input
              </p>
              <Link to="/input" className="text-xs text-orange-400 underline mt-1 block">Go to Manual Input →</Link>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Tabs */}
      <Tabs defaultValue="description">
        <TabsList>
          <TabsTrigger value="description">Description</TabsTrigger>
          <TabsTrigger value="requirements">Requirements</TabsTrigger>
          {md && <TabsTrigger value="analysis">Match Analysis</TabsTrigger>}
        </TabsList>

        <TabsContent value="description">
          <Card><CardContent className="p-5">
            <p className="text-sm text-muted-foreground leading-relaxed whitespace-pre-wrap">
              {job.job_description || 'No description available.'}
            </p>
          </CardContent></Card>
        </TabsContent>

        <TabsContent value="requirements">
          <Card><CardContent className="p-5">
            {job.requirements?.length ? (
              <ul className="space-y-2">
                {job.requirements.map((r, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-muted-foreground">
                    <span className="h-1.5 w-1.5 rounded-full bg-primary mt-2 shrink-0" />{r}
                  </li>
                ))}
              </ul>
            ) : <p className="text-sm text-muted-foreground">No requirements listed.</p>}
            {job.skills_required?.length ? (
              <div className="mt-4 pt-4 border-t border-border">
                <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2">Skills</p>
                <div className="flex flex-wrap gap-2">
                  {job.skills_required.map(s => <Badge key={s} variant="secondary">{s}</Badge>)}
                </div>
              </div>
            ) : null}
          </CardContent></Card>
        </TabsContent>

        {md && (
          <TabsContent value="analysis">
            <div className="space-y-4">
              <Card><CardContent className="p-5">
                <p className="text-sm text-muted-foreground">{md.overall_summary}</p>
              </CardContent></Card>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Card><CardHeader className="pb-2"><CardTitle className="text-sm text-emerald-400">Matched Skills</CardTitle></CardHeader>
                  <CardContent><div className="flex flex-wrap gap-2">
                    {md.matched_skills.map(s => <Badge key={s} variant="success">{s}</Badge>)}
                    {!md.matched_skills.length && <p className="text-xs text-muted-foreground">None</p>}
                  </div></CardContent>
                </Card>
                <Card><CardHeader className="pb-2"><CardTitle className="text-sm text-red-400">Missing Skills</CardTitle></CardHeader>
                  <CardContent><div className="flex flex-wrap gap-2">
                    {md.missing_skills.map(s => <Badge key={s} variant="destructive">{s}</Badge>)}
                    {!md.missing_skills.length && <p className="text-xs text-muted-foreground">None</p>}
                  </div></CardContent>
                </Card>
              </div>

              {md.gaps.length > 0 && (
                <Card><CardHeader className="pb-2"><CardTitle className="text-sm flex items-center gap-2"><AlertTriangle className="h-4 w-4 text-amber-400" />Gaps to Address</CardTitle></CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {md.gaps.map((g, i) => (
                        <div key={i} className="rounded-lg border border-border p-3">
                          <div className="flex items-center gap-2 mb-1">
                            <Badge variant={g.severity === 'critical' ? 'destructive' : g.severity === 'moderate' ? 'warning' : 'secondary'} className="text-[10px]">
                              {g.severity}
                            </Badge>
                            <span className="text-xs font-medium text-muted-foreground">{g.category}</span>
                          </div>
                          <p className="text-sm text-foreground">{g.gap}</p>
                          <p className="text-xs text-muted-foreground mt-1 italic">{g.suggestion}</p>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          </TabsContent>
        )}
      </Tabs>

      {/* Agent Trail */}
      {jobLogs.length > 0 && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center gap-2">
              <Bot className="h-4 w-4 text-primary" />Agent Trail
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="divide-y divide-border max-h-64 overflow-auto">
              {jobLogs.map(log => (
                <div key={log.id} className="flex items-center gap-3 px-4 py-2.5 hover:bg-secondary/20">
                  {log.agent_name && (
                    <span className={cn('inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[10px] font-medium shrink-0', AGENT_COLOR[log.agent_name] ?? 'bg-muted text-muted-foreground border-border')}>
                      <Bot className="h-2.5 w-2.5" />{log.agent_name.replace('Agent', '')}
                    </span>
                  )}
                  <span className="text-xs font-semibold text-primary shrink-0">{log.event}</span>
                  {log.message && <span className="text-xs text-muted-foreground flex-1 truncate">{log.message}</span>}
                  {log.decision && (
                    <span className={cn('text-[9px] font-bold uppercase shrink-0',
                      log.decision === 'proceed' ? 'text-emerald-400' :
                      log.decision === 'await_approval' ? 'text-amber-400' :
                      log.decision === 'fail' ? 'text-red-400' : 'text-muted-foreground'
                    )}>{log.decision}</span>
                  )}
                  <span className="text-[10px] text-muted-foreground shrink-0">{timeAgo(log.created_at)}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
