import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Briefcase, CheckCircle2, AlertTriangle, TrendingUp,
  Zap, RefreshCw, Clock, XCircle,
} from 'lucide-react'
import { jobsApi } from '@/lib/api'
import { StatCard } from '@/components/StatCard'
import { JobCard } from '@/components/JobCard'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { useToast } from '@/hooks/use-toast'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell,
} from 'recharts'
import { useState } from 'react'
import type { Job } from '@/types'

const STATUS_COLORS: Record<string, string> = {
  discovered: '#64748b', analyzing: '#3b82f6', review_required: '#f59e0b',
  tailoring: '#a855f7', ready_to_apply: '#06b6d4', applying: '#6e8dfc',
  applied: '#10b981', waiting_input: '#f97316', failed: '#ef4444',
  skipped: '#475569',
}

export function Dashboard() {
  const qc = useQueryClient()
  const { toast } = useToast()
  const [discoverKeywords, setDiscoverKeywords] = useState('Software Engineer')
  const [discoverLocation, setDiscoverLocation] = useState('')
  const [discovering, setDiscovering] = useState(false)

  const { data: stats = {} } = useQuery({ queryKey: ['job-stats'], queryFn: jobsApi.stats, refetchInterval: 10_000 })
  const { data: jobs = [], isLoading } = useQuery<Job[]>({ queryKey: ['jobs'], queryFn: () => jobsApi.list({ limit: 8 }), refetchInterval: 10_000 })

  const analyseMutation = useMutation({
    mutationFn: (id: string) => jobsApi.analyse(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['jobs'] }); qc.invalidateQueries({ queryKey: ['job-stats'] }) },
    onError: (e: Error) => toast({ title: 'Analysis failed', description: e.message, variant: 'destructive' }),
  })

  const applyMutation = useMutation({
    mutationFn: (id: string) => jobsApi.apply(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['jobs'] }); toast({ title: 'Application submitted!', variant: 'default' }) },
    onError: (e: Error) => toast({ title: 'Apply failed', description: e.message, variant: 'destructive' }),
  })

  async function handleDiscover() {
    setDiscovering(true)
    try {
      const result = await jobsApi.discover({ keywords: discoverKeywords, location: discoverLocation })
      toast({ title: `Discovered ${result.discovered} jobs`, variant: 'default' })
      qc.invalidateQueries({ queryKey: ['jobs'] })
      qc.invalidateQueries({ queryKey: ['job-stats'] })
    } catch (e: any) {
      toast({ title: 'Discovery failed', description: e.message, variant: 'destructive' })
    } finally {
      setDiscovering(false)
    }
  }

  const total = Object.values(stats as Record<string, number>).reduce((a, b) => a + b, 0)
  const applied = (stats as any).applied ?? 0
  const waiting = (stats as any).waiting_input ?? 0
  const failed = (stats as any).failed ?? 0

  const chartData = Object.entries(stats as Record<string, number>).map(([k, v]) => ({
    name: k.replace('_', ' '), value: v, color: STATUS_COLORS[k] ?? '#6e8dfc',
  }))

  const recentJobs = jobs.slice(0, 6)

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold gradient-text">Dashboard</h1>
          <p className="text-muted-foreground text-sm mt-0.5">Your job application command centre</p>
        </div>
        <Button onClick={() => { qc.invalidateQueries({ queryKey: ['jobs'] }); qc.invalidateQueries({ queryKey: ['job-stats'] }) }} variant="outline" size="sm">
          <RefreshCw className="h-3.5 w-3.5 mr-1.5" /> Refresh
        </Button>
      </div>

      {/* Discover bar */}
      <Card className="border-primary/20 bg-gradient-to-r from-primary/5 to-transparent">
        <CardContent className="p-5">
          <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-3">Discover New Jobs</p>
          <div className="flex gap-3 flex-wrap">
            <input
              className="flex h-9 flex-1 min-w-48 rounded-lg border border-border bg-secondary/50 px-3 py-1 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
              placeholder="Keywords (e.g. React Developer)"
              value={discoverKeywords}
              onChange={e => setDiscoverKeywords(e.target.value)}
            />
            <input
              className="flex h-9 w-48 rounded-lg border border-border bg-secondary/50 px-3 py-1 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
              placeholder="Location (optional)"
              value={discoverLocation}
              onChange={e => setDiscoverLocation(e.target.value)}
            />
            <Button onClick={handleDiscover} disabled={discovering} variant="glow" className="gap-2">
              {discovering ? <><RefreshCw className="h-3.5 w-3.5 animate-spin" /> Searching…</> : <><Zap className="h-3.5 w-3.5" /> Find Jobs</>}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Stats row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Total Jobs" value={total} icon={Briefcase} color="text-primary" />
        <StatCard title="Applied" value={applied} icon={CheckCircle2} color="text-emerald-400" />
        <StatCard title="Awaiting Input" value={waiting} icon={Clock} color="text-amber-400" />
        <StatCard title="Failed" value={failed} icon={XCircle} color="text-red-400" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Chart */}
        <Card className="lg:col-span-1">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center gap-2"><TrendingUp className="h-4 w-4 text-primary" />Status Breakdown</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={chartData} margin={{ top: 0, right: 0, bottom: 20, left: -20 }}>
                <XAxis dataKey="name" tick={{ fontSize: 9, fill: '#64748b' }} angle={-30} textAnchor="end" />
                <YAxis tick={{ fontSize: 10, fill: '#64748b' }} />
                <Tooltip
                  contentStyle={{ background: 'hsl(222 47% 7%)', border: '1px solid hsl(222 30% 14%)', borderRadius: 8, fontSize: 12 }}
                  cursor={{ fill: 'rgba(255,255,255,0.03)' }}
                />
                <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                  {chartData.map((entry, i) => <Cell key={i} fill={entry.color} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Waiting alerts */}
        <Card className="lg:col-span-2">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center gap-2"><AlertTriangle className="h-4 w-4 text-amber-400" />Needs Attention</CardTitle>
          </CardHeader>
          <CardContent>
            {jobs.filter(j => ['waiting_input', 'review_required', 'failed'].includes(j.status)).length === 0 ? (
              <p className="text-sm text-muted-foreground py-4 text-center">All clear — no pending actions</p>
            ) : (
              <div className="space-y-2">
                {jobs.filter(j => ['waiting_input', 'review_required', 'failed'].includes(j.status)).slice(0, 4).map(job => (
                  <div key={job.id} className="flex items-center gap-3 rounded-lg border border-border p-3">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">{job.title}</p>
                      <p className="text-xs text-muted-foreground">{job.company}</p>
                    </div>
                    <span className="text-xs text-amber-400 capitalize">{job.status.replace('_', ' ')}</span>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Recent jobs */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-base font-semibold">Recent Jobs</h2>
          <Button variant="ghost" size="sm" asChild><a href="/jobs">View all →</a></Button>
        </div>
        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[...Array(4)].map((_, i) => <div key={i} className="h-40 skeleton rounded-xl" />)}
          </div>
        ) : recentJobs.length === 0 ? (
          <Card>
            <CardContent className="py-12 text-center">
              <Briefcase className="h-8 w-8 text-muted-foreground mx-auto mb-3" />
              <p className="text-muted-foreground">No jobs yet. Use the search bar above to discover jobs.</p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {recentJobs.map(job => (
              <JobCard
                key={job.id}
                job={job}
                onAnalyse={() => analyseMutation.mutate(job.id)}
                onApply={() => applyMutation.mutate(job.id)}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
