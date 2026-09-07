import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { Upload, FileText, Eye, Sparkles } from 'lucide-react'
import { resumesApi } from '@/lib/api'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import { useToast } from '@/hooks/use-toast'
import { useQueryClient } from '@tanstack/react-query'
import type { Resume } from '@/types'

export function ResumePreview() {
  const qc = useQueryClient()
  const { toast } = useToast()
  const [uploading, setUploading] = useState(false)
  const [selectedId, setSelectedId] = useState<string | null>(null)

  const { data: resumes = [], isLoading } = useQuery<Resume[]>({
    queryKey: ['resumes'],
    queryFn: resumesApi.list,
  })

  const { data: textData } = useQuery({
    queryKey: ['resume-text', selectedId],
    queryFn: () => resumesApi.text(selectedId!),
    enabled: !!selectedId,
  })

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    setUploading(true)
    try {
      await resumesApi.upload(file, true)
      toast({ title: 'Resume uploaded & indexed!', variant: 'default' })
      qc.invalidateQueries({ queryKey: ['resumes'] })
    } catch (err: any) {
      toast({ title: 'Upload failed', description: err.message, variant: 'destructive' })
    } finally {
      setUploading(false)
    }
  }

  const base = resumes.find(r => r.is_base)
  const tailored = resumes.filter(r => !r.is_base)
  const selected = resumes.find(r => r.id === selectedId) ?? base ?? resumes[0]

  return (
    <div className="space-y-6 animate-fade-in max-w-5xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold gradient-text">Resume Preview</h1>
          <p className="text-sm text-muted-foreground mt-0.5">View, compare, and manage all resume versions</p>
        </div>
        <label className="cursor-pointer">
          <input type="file" accept=".pdf,.docx,.doc,.txt" className="hidden" onChange={handleUpload} />
          <Button variant="glow" size="sm" disabled={uploading} asChild>
            <span>{uploading ? 'Uploading…' : <><Upload className="h-3.5 w-3.5 mr-1.5" />Upload Resume</>}</span>
          </Button>
        </label>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-3 gap-4">{[...Array(3)].map((_, i) => <div key={i} className="h-24 skeleton rounded-xl" />)}</div>
      ) : resumes.length === 0 ? (
        <Card className="border-dashed border-2 border-border">
          <CardContent className="py-16 text-center">
            <Upload className="h-10 w-10 text-muted-foreground mx-auto mb-4" />
            <p className="text-foreground font-medium">No resumes yet</p>
            <p className="text-sm text-muted-foreground mt-1">Upload a PDF or DOCX to get started</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Version list */}
          <div className="space-y-2">
            <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground px-1">Versions</p>
            {resumes.map(r => (
              <button
                key={r.id}
                onClick={() => setSelectedId(r.id)}
                className={`w-full text-left rounded-lg border p-3 transition-all ${r.id === (selectedId ?? base?.id ?? resumes[0]?.id) ? 'border-primary/40 bg-primary/5' : 'border-border hover:border-primary/20'}`}
              >
                <div className="flex items-center gap-2">
                  <FileText className="h-3.5 w-3.5 text-primary shrink-0" />
                  <p className="text-xs font-medium truncate">{r.version}</p>
                </div>
                {r.is_base && <Badge variant="success" className="text-[9px] mt-1">Base</Badge>}
                {r.tailored_for_job && <Badge variant="info" className="text-[9px] mt-1">Tailored</Badge>}
                <p className="text-[10px] text-muted-foreground mt-1">{new Date(r.created_at).toLocaleDateString()}</p>
              </button>
            ))}
          </div>

          {/* Preview panel */}
          <Card className="lg:col-span-3">
            <CardHeader className="pb-3 flex-row items-center justify-between">
              <CardTitle className="text-sm flex items-center gap-2">
                <Eye className="h-4 w-4 text-primary" />
                {selected?.version ?? 'Select a resume'}
              </CardTitle>
              {selected?.tailored_for_job && (
                <Badge variant="info" className="gap-1"><Sparkles className="h-3 w-3" />AI Tailored</Badge>
              )}
            </CardHeader>
            <CardContent>
              {selected?.diff_summary && (
                <div className="mb-4 rounded-lg border border-primary/20 bg-primary/5 p-3">
                  <p className="text-xs font-semibold text-primary mb-1">AI Tailoring Summary</p>
                  <p className="text-xs text-muted-foreground">{selected.diff_summary}</p>
                </div>
              )}
              <pre className="text-xs text-muted-foreground leading-relaxed whitespace-pre-wrap font-mono bg-secondary/30 rounded-lg p-4 max-h-[60vh] overflow-auto">
                {textData?.text ?? (selected ? 'Loading…' : 'Select a resume version from the left')}
              </pre>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}
