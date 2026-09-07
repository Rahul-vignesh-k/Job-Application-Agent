import { Link } from 'react-router-dom'
import { MapPin, DollarSign, Building2, Clock, Zap, ArrowUpRight } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { cn, formatSalary, timeAgo, statusConfig, scoreBg, platformIcon } from '@/lib/utils'
import type { Job } from '@/types'

interface Props {
  job: Job
  onAnalyse?: () => void
  onApply?: () => void
}

export function JobCard({ job, onAnalyse, onApply }: Props) {
  const sc = statusConfig(job.status)
  const hasScore = job.match_score !== undefined && job.match_score !== null

  return (
    <Card className="group relative overflow-hidden transition-all duration-200 hover:border-primary/30 hover:shadow-lg hover:shadow-primary/5">
      {/* Platform tag */}
      <div className="absolute top-0 right-0 flex items-center gap-0">
        <span className="px-2 py-1 text-[10px] font-bold uppercase tracking-widest text-muted-foreground bg-secondary/80 rounded-bl-lg">
          {platformIcon(job.platform)} {job.platform}
        </span>
      </div>

      <CardContent className="p-5">
        <div className="flex items-start gap-4">
          {/* Company avatar */}
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-primary/20 to-primary/5 ring-1 ring-primary/20 text-primary font-bold text-sm">
            {job.company.charAt(0)}
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-2 mb-1">
              <h3 className="font-semibold text-foreground truncate pr-16 group-hover:text-primary transition-colors">
                {job.title}
              </h3>
            </div>

            <div className="flex items-center flex-wrap gap-3 text-xs text-muted-foreground mb-3">
              <span className="flex items-center gap-1"><Building2 className="h-3 w-3" />{job.company}</span>
              {job.location && <span className="flex items-center gap-1"><MapPin className="h-3 w-3" />{job.location}</span>}
              {(job.salary_min || job.salary_max) && (
                <span className="flex items-center gap-1">
                  <DollarSign className="h-3 w-3" />
                  {formatSalary(job.salary_min, job.salary_max, job.salary_currency)}
                </span>
              )}
              <span className="flex items-center gap-1"><Clock className="h-3 w-3" />{timeAgo(job.discovered_at)}</span>
            </div>

            <div className="flex items-center flex-wrap gap-2">
              {/* Status badge */}
              <span className={cn('inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium', sc.color)}>
                <span className={cn('h-1.5 w-1.5 rounded-full', sc.dot)} />
                {sc.label}
              </span>

              {/* Easy apply */}
              {job.is_easy_apply && (
                <Badge variant="info" className="text-[10px]">
                  <Zap className="h-2.5 w-2.5" /> Easy Apply
                </Badge>
              )}

              {/* Job classification */}
              {job.job_classification && (
                <Badge
                  className={`text-[10px] ${job.job_classification === 'Internship' ? 'border-violet-500/20 bg-violet-500/10 text-violet-400' : 'border-sky-500/20 bg-sky-500/10 text-sky-400'}`}
                >
                  {job.job_classification}
                </Badge>
              )}

              {/* Remote tag */}
              {job.remote_type && (
                <Badge variant="secondary" className="text-[10px] capitalize">{job.remote_type}</Badge>
              )}

              {/* Match score */}
              {hasScore && (
                <span className={cn('inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-bold', scoreBg(job.match_score!))}>
                  {job.match_score}% match
                </span>
              )}
            </div>

            {/* Score bar */}
            {hasScore && (
              <div className="mt-3">
                <Progress
                  value={job.match_score}
                  className="h-1"
                  indicatorClassName={cn(
                    job.match_score! >= 85 ? 'bg-emerald-500' :
                    job.match_score! >= 65 ? 'bg-amber-500' : 'bg-red-500'
                  )}
                />
              </div>
            )}
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2 mt-4 pt-4 border-t border-border/50">
          <Link to={`/jobs/${job.id}`} className="flex-1">
            <Button variant="outline" size="sm" className="w-full gap-1.5">
              View Details <ArrowUpRight className="h-3.5 w-3.5" />
            </Button>
          </Link>
          {job.status === 'discovered' && onAnalyse && (
            <Button size="sm" onClick={onAnalyse} className="gap-1.5">
              <Zap className="h-3.5 w-3.5" /> Analyse
            </Button>
          )}
          {(job.status === 'ready_to_apply') && onApply && (
            <Button size="sm" variant="success" onClick={onApply} className="gap-1.5">
              Apply Now
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
