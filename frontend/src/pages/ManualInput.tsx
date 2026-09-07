import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { Plus, Trash2, Shield, Database, MessageSquarePlus } from 'lucide-react'
import { jobsApi, answersApi } from '@/lib/api'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Badge } from '@/components/ui/badge'
import { useToast } from '@/hooks/use-toast'
import type { SavedAnswer, PendingField, Job } from '@/types'

export function ManualInput() {
  const qc = useQueryClient()
  const { toast } = useToast()

  const { data: answers = [] } = useQuery<SavedAnswer[]>({ queryKey: ['answers'], queryFn: answersApi.list })
  const { data: jobs = [] } = useQuery<Job[]>({
    queryKey: ['jobs-waiting'],
    queryFn: () => jobsApi.list({ status: 'waiting_input', limit: 50 }),
  })

  // New answer form
  const [newKey, setNewKey] = useState('')
  const [newLabel, setNewLabel] = useState('')
  const [newAnswer, setNewAnswer] = useState('')
  const [isSensitive, setIsSensitive] = useState(false)

  // Pending field answers state
  const [pendingAnswers, setPendingAnswers] = useState<Record<string, string>>({})

  const saveMut = useMutation({
    mutationFn: () => answersApi.save({ field_key: newKey, field_label: newLabel, answer: newAnswer, is_sensitive: isSensitive }),
    onSuccess: () => {
      toast({ title: 'Answer saved' })
      setNewKey(''); setNewLabel(''); setNewAnswer(''); setIsSensitive(false)
      qc.invalidateQueries({ queryKey: ['answers'] })
    },
    onError: (e: Error) => toast({ title: 'Save failed', description: e.message, variant: 'destructive' }),
  })

  const deleteMut = useMutation({
    mutationFn: (key: string) => answersApi.delete(key),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['answers'] }) },
  })

  function PendingJobFields({ job }: { job: Job }) {
    const { data: fields = [] } = useQuery<PendingField[]>({
      queryKey: ['pending-fields', job.id],
      queryFn: () => jobsApi.pendingFields(job.id),
    })

    const resolveMut = useMutation({
      mutationFn: (answers: Record<string, string>) => jobsApi.resolveFields(job.id, answers),
      onSuccess: () => {
        toast({ title: 'Fields resolved — resuming application' })
        qc.invalidateQueries({ queryKey: ['jobs-waiting'] })
        qc.invalidateQueries({ queryKey: ['pending-fields', job.id] })
      },
      onError: (e: Error) => toast({ title: 'Failed', description: e.message, variant: 'destructive' }),
    })

    if (!fields.length) return null
    const localAnswers = { ...pendingAnswers }

    return (
      <Card className="border-orange-500/30">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm flex items-center gap-2 text-orange-300">
            <MessageSquarePlus className="h-4 w-4" />
            {job.title} @ {job.company}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {fields.map(field => (
            <div key={field.id}>
              <Label className="text-foreground font-medium">
                {field.field_label || field.field_key}
                {field.field_type !== 'text' && (
                  <Badge variant="secondary" className="ml-2 text-[10px]">{field.field_type}</Badge>
                )}
              </Label>
              {field.field_type === 'select' && field.options?.length ? (
                <select
                  className="mt-1.5 flex h-9 w-full rounded-lg border border-border bg-secondary/50 px-3 py-1 text-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                  value={localAnswers[field.id] ?? ''}
                  onChange={e => setPendingAnswers(prev => ({ ...prev, [field.id]: e.target.value }))}
                >
                  <option value="">Select…</option>
                  {field.options.map(o => <option key={o} value={o}>{o}</option>)}
                </select>
              ) : (
                <Input
                  className="mt-1.5"
                  placeholder={`Enter ${field.field_label ?? field.field_key}`}
                  value={localAnswers[field.id] ?? ''}
                  onChange={e => setPendingAnswers(prev => ({ ...prev, [field.id]: e.target.value }))}
                />
              )}
            </div>
          ))}
          <Button
            onClick={() => {
              const answersForJob = Object.fromEntries(
                fields.map(f => [f.id, localAnswers[f.id] ?? ''])
              )
              resolveMut.mutate(answersForJob)
            }}
            disabled={resolveMut.isPending}
            className="w-full"
          >
            {resolveMut.isPending ? 'Submitting…' : 'Submit & Resume Application'}
          </Button>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6 animate-fade-in max-w-3xl">
      <div>
        <h1 className="text-2xl font-bold gradient-text">Manual Input</h1>
        <p className="text-sm text-muted-foreground mt-0.5">Provide answers for unknown form fields and save them for reuse</p>
      </div>

      {/* Pending jobs */}
      {jobs.length > 0 && (
        <div className="space-y-4">
          <p className="text-sm font-semibold text-orange-300 flex items-center gap-2">
            <MessageSquarePlus className="h-4 w-4" /> {jobs.length} application{jobs.length > 1 ? 's' : ''} waiting for input
          </p>
          {jobs.map(job => <PendingJobFields key={job.id} job={job} />)}
        </div>
      )}

      {/* New answer form */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm flex items-center gap-2">
            <Plus className="h-4 w-4 text-primary" />Add Saved Answer
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label>Field Key</Label>
              <Input className="mt-1.5" placeholder="e.g. expected_salary" value={newKey} onChange={e => setNewKey(e.target.value)} />
            </div>
            <div>
              <Label>Field Label</Label>
              <Input className="mt-1.5" placeholder="e.g. Expected Salary" value={newLabel} onChange={e => setNewLabel(e.target.value)} />
            </div>
          </div>
          <div>
            <Label>Answer</Label>
            <Input className="mt-1.5" placeholder="Your answer" value={newAnswer} onChange={e => setNewAnswer(e.target.value)} />
          </div>
          <div className="flex items-center gap-3">
            <Switch checked={isSensitive} onCheckedChange={setIsSensitive} id="sensitive" />
            <Label htmlFor="sensitive" className="flex items-center gap-1.5 cursor-pointer">
              <Shield className="h-3.5 w-3.5 text-amber-400" />
              Mark as sensitive (will ask confirmation before auto-filling)
            </Label>
          </div>
          <Button onClick={() => saveMut.mutate()} disabled={saveMut.isPending || !newKey || !newAnswer} className="w-full">
            {saveMut.isPending ? 'Saving…' : 'Save Answer'}
          </Button>
        </CardContent>
      </Card>

      {/* Saved answers table */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm flex items-center gap-2">
            <Database className="h-4 w-4 text-primary" />Saved Answers ({answers.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          {answers.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-4">No saved answers yet</p>
          ) : (
            <div className="space-y-2">
              {answers.map(a => (
                <div key={a.id} className="flex items-center gap-3 rounded-lg border border-border p-3 group">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <p className="text-xs font-mono text-primary truncate">{a.field_key}</p>
                      {a.is_sensitive && <Shield className="h-3 w-3 text-amber-400 shrink-0" />}
                      <Badge variant="secondary" className="text-[9px]">{a.source}</Badge>
                    </div>
                    {a.field_label && <p className="text-xs text-muted-foreground">{a.field_label}</p>}
                    <p className="text-sm mt-0.5 truncate">{a.answer}</p>
                  </div>
                  <Button
                    variant="ghost" size="icon"
                    className="opacity-0 group-hover:opacity-100 h-7 w-7 text-red-400 hover:text-red-300"
                    onClick={() => deleteMut.mutate(a.field_key)}
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </Button>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
