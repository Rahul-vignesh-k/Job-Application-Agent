import { LucideIcon } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { cn } from '@/lib/utils'

interface Props {
  title: string
  value: string | number
  change?: string
  positive?: boolean
  icon: LucideIcon
  color?: string
}

export function StatCard({ title, value, change, positive, icon: Icon, color = 'text-primary' }: Props) {
  return (
    <Card className="overflow-hidden">
      <CardContent className="p-5">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-1">{title}</p>
            <p className="text-2xl font-bold text-foreground tabular-nums">{value}</p>
            {change && (
              <p className={cn('text-xs mt-1', positive ? 'text-emerald-400' : 'text-red-400')}>
                {positive ? '↑' : '↓'} {change}
              </p>
            )}
          </div>
          <div className={cn('flex h-9 w-9 items-center justify-center rounded-lg bg-current/10', color)}>
            <Icon className={cn('h-4.5 w-4.5', color)} style={{ height: '18px', width: '18px' }} />
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
