import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { Search, Filter, RefreshCw, Zap } from 'lucide-react'
import { jobsApi } from '@/lib/api'
import { JobCard } from '@/components/JobCard'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { useToast } from '@/hooks/use-toast'
import type { Job } from '@/types'

const STATUSES = ['all','discovered','analyzing','review_required','tailoring','ready_to_apply','applying','applied','waiting_input','failed','skipped']
const PLATFORMS = ['all','linkedin','naukri','indeed','glassdoor','manual']

export function JobQueue() {
  const qc = useQueryClient()
  const { toast } = useToast()
  const [statusFilter, setStatusFilter] = useState('all')
  const [platformFilter, setPlatformFilter] = useState('all')
  const [search, setSearch] = useState('')

  const params: Record<string, string | number> = { limit: 200 }
  if (statusFilter !== 'all') params.status = statusFilter
  if (platformFilter !== 'all') params.platform = platformFilter

  const { data: jobs = [], isLoading, refetch } = useQuery<Job[]>({
    queryKey: ['jobs', statusFilter, platformFilter],
    queryFn: () => jobsApi.list(params),
    refetchInterval: 15_000,
  })

  const analyseMutation = useMutation({
    mutationFn: (id: string) => jobsApi.analyse(id),
    onSuccess: (_, id) => {
      toast({ title: 'Analysis complete' })
      qc.invalidateQueries({ queryKey: ['jobs'] })
    },
    onError: (e: Error) => toast({ title: 'Failed', description: e.message, variant: 'destructive' }),
  })

  const applyMutation = useMutation({
    mutationFn: (id: string) => jobsApi.apply(id),
    onSuccess: () => { toast({ title: 'Applied!' }); qc.invalidateQueries({ queryKey: ['jobs'] }) },
    onError: (e: Error) => toast({ title: 'Apply failed', description: e.message, variant: 'destructive' }),
  })

  const filtered = jobs.filter(j => {
    if (!search) return true
    const q = search.toLowerCase()
    return j.title.toLowerCase().includes(q) || j.company.toLowerCase().includes(q)
  })

  async function analyseAll() {
    const toAnalyse = filtered.filter(j => j.status === 'discovered')
    for (const j of toAnalyse) {
      await analyseMutation.mutateAsync(j.id).catch(() => {})
    }
    toast({ title: `Analysed ${toAnalyse.length} jobs` })
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold gradient-text">Job Queue</h1>
          <p className="text-sm text-muted-foreground mt-0.5">{filtered.length} jobs</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => refetch()}>
            <RefreshCw className="h-3.5 w-3.5 mr-1.5" /> Refresh
          </Button>
          <Button size="sm" onClick={analyseAll} disabled={analyseMutation.isPending} variant="glow">
            <Zap className="h-3.5 w-3.5 mr-1.5" /> Analyse All
          </Button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <div className="relative flex-1 min-w-48">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
          <Input placeholder="Search jobs…" className="pl-9" value={search} onChange={e => setSearch(e.target.value)} />
        </div>
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-44"><Filter className="h-3.5 w-3.5 mr-1.5 text-muted-foreground" /><SelectValue /></SelectTrigger>
          <SelectContent>
            {STATUSES.map(s => <SelectItem key={s} value={s}>{s === 'all' ? 'All Statuses' : s.replace('_', ' ')}</SelectItem>)}
          </SelectContent>
        </Select>
        <Select value={platformFilter} onValueChange={setPlatformFilter}>
          <SelectTrigger className="w-36"><SelectValue /></SelectTrigger>
          <SelectContent>
            {PLATFORMS.map(p => <SelectItem key={p} value={p}>{p === 'all' ? 'All Platforms' : p}</SelectItem>)}
          </SelectContent>
        </Select>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[...Array(6)].map((_, i) => <div key={i} className="h-44 skeleton rounded-xl" />)}
        </div>
      ) : filtered.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-24 text-center">
          <div className="h-14 w-14 rounded-full bg-secondary flex items-center justify-center mb-4">
            <Search className="h-6 w-6 text-muted-foreground" />
          </div>
          <p className="text-foreground font-medium">No jobs found</p>
          <p className="text-sm text-muted-foreground mt-1">Try adjusting filters or discover new jobs from Dashboard</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filtered.map(job => (
            <JobCard
              key={job.id}
              job={job}
              onAnalyse={job.status === 'discovered' ? () => analyseMutation.mutate(job.id) : undefined}
              onApply={job.status === 'ready_to_apply' ? () => applyMutation.mutate(job.id) : undefined}
            />
          ))}
        </div>
      )}
    </div>
  )
}
