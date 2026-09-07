import { useQuery } from '@tanstack/react-query'
import { jobsApi } from '@/lib/api'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { ScoreRing } from '@/components/ScoreRing'
import { Progress } from '@/components/ui/progress'
import { BarChart3, AlertTriangle, CheckCircle2 } from 'lucide-react'
import { cn, scoreBg } from '@/lib/utils'
import type { Job } from '@/types'

export function MatchReport() {
  const { data: jobs = [], isLoading } = useQuery<Job[]>({
    queryKey: ['jobs-matched'],
    queryFn: () => jobsApi.list({ limit: 200 }),
  })

  const analysed = jobs.filter(j => j.match_score !== undefined && j.match_score !== null)
  const avgScore = analysed.length ? Math.round(analysed.reduce((s, j) => s + j.match_score!, 0) / analysed.length) : 0
  const autoApply = analysed.filter(j => j.match_score! >= 85)
  const reviewReq = analysed.filter(j => j.match_score! < 85 && j.match_score! >= 50)
  const lowMatch = analysed.filter(j => j.match_score! < 50)

  return (
    <div className="space-y-6 animate-fade-in max-w-4xl">
      <div>
        <h1 className="text-2xl font-bold gradient-text">Match Report</h1>
        <p className="text-sm text-muted-foreground mt-0.5">Gemini + RAG resume analysis across all jobs</p>
      </div>

      {/* Summary stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="border-primary/20">
          <CardContent className="p-5 flex flex-col items-center">
            <ScoreRing score={avgScore} size={64} strokeWidth={5} />
            <p className="text-xs text-muted-foreground mt-2">Avg Score</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-5">
            <p className="text-2xl font-bold text-emerald-400">{autoApply.length}</p>
            <p className="text-xs text-muted-foreground mt-1">Auto-Apply Ready</p>
            <p className="text-[10px] text-muted-foreground">≥ 85%</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-5">
            <p className="text-2xl font-bold text-amber-400">{reviewReq.length}</p>
            <p className="text-xs text-muted-foreground mt-1">Review Required</p>
            <p className="text-[10px] text-muted-foreground">50–84%</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-5">
            <p className="text-2xl font-bold text-red-400">{lowMatch.length}</p>
            <p className="text-xs text-muted-foreground mt-1">Low Match</p>
            <p className="text-[10px] text-muted-foreground">{'< '}50%</p>
          </CardContent>
        </Card>
      </div>

      {isLoading ? (
        <div className="space-y-3">{[...Array(4)].map((_, i) => <div key={i} className="h-20 skeleton rounded-xl" />)}</div>
      ) : analysed.length === 0 ? (
        <Card><CardContent className="py-12 text-center">
          <BarChart3 className="h-8 w-8 text-muted-foreground mx-auto mb-3" />
          <p className="text-muted-foreground">No analysed jobs yet. Run analysis from Job Queue.</p>
        </CardContent></Card>
      ) : (
        <div className="space-y-3">
          {analysed.sort((a, b) => b.match_score! - a.match_score!).map(job => (
            <Card key={job.id} className="hover:border-primary/30 transition-colors">
              <CardContent className="p-4">
                <div className="flex items-center gap-4">
                  <ScoreRing score={job.match_score!} size={56} strokeWidth={4} />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <p className="font-medium text-sm">{job.title}</p>
                      <span className={cn('text-xs font-bold rounded-full border px-2 py-0.5', scoreBg(job.match_score!))}>
                        {job.match_score}%
                      </span>
                    </div>
                    <p className="text-xs text-muted-foreground mt-0.5">{job.company} · {job.platform}</p>
                    <Progress
                      value={job.match_score!}
                      className="h-1 mt-2"
                      indicatorClassName={cn(
                        job.match_score! >= 85 ? 'bg-emerald-500' :
                        job.match_score! >= 65 ? 'bg-amber-500' : 'bg-red-500'
                      )}
                    />
                  </div>
                  <div className="shrink-0">
                    {job.match_score! >= 85 ? (
                      <CheckCircle2 className="h-5 w-5 text-emerald-400" />
                    ) : (
                      <AlertTriangle className="h-5 w-5 text-amber-400" />
                    )}
                  </div>
                </div>

                {job.match_details?.missing_skills?.length ? (
                  <div className="mt-3 pt-3 border-t border-border/50">
                    <p className="text-[10px] uppercase tracking-wider text-muted-foreground mb-1.5">Missing Skills</p>
                    <div className="flex flex-wrap gap-1.5">
                      {job.match_details.missing_skills.slice(0, 6).map(s => (
                        <Badge key={s} variant="destructive" className="text-[10px]">{s}</Badge>
                      ))}
                      {job.match_details.missing_skills.length > 6 && (
                        <span className="text-[10px] text-muted-foreground">+{job.match_details.missing_skills.length - 6} more</span>
                      )}
                    </div>
                  </div>
                ) : null}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
