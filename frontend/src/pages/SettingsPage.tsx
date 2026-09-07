import { useQuery, useMutation } from '@tanstack/react-query'
import { useState, useEffect } from 'react'
import { settingsApi } from '@/lib/api'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Separator } from '@/components/ui/separator'
import { useToast } from '@/hooks/use-toast'
import { Settings, User, Zap, CheckCircle2, XCircle, Target } from 'lucide-react'
import type { AppSettings } from '@/types'

export function SettingsPage() {
  const { toast } = useToast()
  const { data: settings, isLoading } = useQuery<AppSettings>({ queryKey: ['settings'], queryFn: settingsApi.get })

  const [form, setForm] = useState<Partial<AppSettings>>({})
  useEffect(() => { if (settings) setForm(settings) }, [settings])

  const saveMut = useMutation({
    mutationFn: () => settingsApi.update(form as Record<string, unknown>),
    onSuccess: () => toast({ title: 'Settings saved' }),
    onError: (e: Error) => toast({ title: 'Save failed', description: e.message, variant: 'destructive' }),
  })

  const set = (key: keyof AppSettings, val: string | number) => setForm(prev => ({ ...prev, [key]: val }))

  if (isLoading) return <div className="space-y-4">{[...Array(3)].map((_, i) => <div key={i} className="h-40 skeleton rounded-xl" />)}</div>

  return (
    <div className="space-y-6 animate-fade-in max-w-3xl">
      <div>
        <h1 className="text-2xl font-bold gradient-text">Settings</h1>
        <p className="text-sm text-muted-foreground mt-0.5">Configure your profile, credentials, and agent behaviour</p>
      </div>

      {/* AI Status */}
      <Card className="border-primary/20">
        <CardContent className="p-5 flex items-center gap-4">
          <div className={`h-10 w-10 rounded-lg flex items-center justify-center ${settings?.gemini_configured ? 'bg-emerald-500/10' : 'bg-red-500/10'}`}>
            {settings?.gemini_configured ? <CheckCircle2 className="h-5 w-5 text-emerald-400" /> : <XCircle className="h-5 w-5 text-red-400" />}
          </div>
          <div>
            <p className="font-medium text-sm">Gemini API</p>
            <p className="text-xs text-muted-foreground">{settings?.gemini_configured ? `Connected · ${settings.gemini_model}` : 'Not configured — set GEMINI_API_KEY in .env'}</p>
          </div>
        </CardContent>
      </Card>

      {/* User Profile */}
      <Card>
        <CardHeader className="pb-4">
          <CardTitle className="text-sm flex items-center gap-2"><User className="h-4 w-4 text-primary" />Profile</CardTitle>
          <CardDescription>Used to auto-fill job application forms</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div><Label>Full Name</Label><Input className="mt-1.5" value={form.user_full_name ?? ''} onChange={e => set('user_full_name', e.target.value)} /></div>
            <div><Label>Email</Label><Input className="mt-1.5" type="email" value={form.user_email ?? ''} onChange={e => set('user_email', e.target.value)} /></div>
            <div><Label>Phone</Label><Input className="mt-1.5" value={form.user_phone ?? ''} onChange={e => set('user_phone', e.target.value)} /></div>
            <div><Label>Location</Label><Input className="mt-1.5" value={form.user_location ?? ''} onChange={e => set('user_location', e.target.value)} /></div>
            <div><Label>Years Experience</Label><Input className="mt-1.5" type="number" value={form.user_years_experience ?? 0} onChange={e => set('user_years_experience', parseInt(e.target.value))} /></div>
            <div><Label>Notice Period</Label><Input className="mt-1.5" value={form.user_notice_period ?? ''} onChange={e => set('user_notice_period', e.target.value)} /></div>
            <div>
              <Label>Expected Salary — Internship</Label>
              <p className="text-[11px] text-muted-foreground mb-1">Used when job is classified as Internship</p>
              <Input className="mt-1" placeholder="e.g. 25k/month" value={form.user_expected_salary_intern ?? ''} onChange={e => set('user_expected_salary_intern', e.target.value)} />
            </div>
            <div>
              <Label>Expected Salary — FTE</Label>
              <p className="text-[11px] text-muted-foreground mb-1">Used when job is classified as Full-Time</p>
              <Input className="mt-1" placeholder="e.g. 7 LPA+" value={form.user_expected_salary_fte ?? ''} onChange={e => set('user_expected_salary_fte', e.target.value)} />
            </div>
          </div>
          <Separator />
          <div className="grid grid-cols-1 gap-4">
            <div><Label>LinkedIn URL</Label><Input className="mt-1.5" value={form.user_linkedin_url ?? ''} onChange={e => set('user_linkedin_url', e.target.value)} /></div>
            <div><Label>GitHub URL</Label><Input className="mt-1.5" value={form.user_github_url ?? ''} onChange={e => set('user_github_url', e.target.value)} /></div>
            <div><Label>Portfolio URL</Label><Input className="mt-1.5" placeholder="Personal site (used first for portfolio fields)" value={form.user_portfolio_url ?? ''} onChange={e => set('user_portfolio_url', e.target.value)} /></div>
            <div>
              <Label>LeetCode URL</Label>
              <p className="text-[11px] text-muted-foreground mb-1">Fallback for coding-profile / website fields when portfolio is empty</p>
              <Input className="mt-1" placeholder="https://leetcode.com/yourusername" value={form.user_leetcode_url ?? ''} onChange={e => set('user_leetcode_url', e.target.value)} />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Agent settings */}
      <Card>
        <CardHeader className="pb-4">
          <CardTitle className="text-sm flex items-center gap-2"><Target className="h-4 w-4 text-primary" />Agent Behaviour</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label>Auto-Apply Threshold (%)</Label>
              <p className="text-xs text-muted-foreground mb-1.5">Jobs above this score auto-apply</p>
              <Input type="number" min={50} max={100} value={form.auto_apply_threshold ?? 85} onChange={e => set('auto_apply_threshold', parseInt(e.target.value))} />
            </div>
            <div>
              <Label>Max Applications / Day</Label>
              <p className="text-xs text-muted-foreground mb-1.5">Safety limit</p>
              <Input type="number" min={1} max={100} value={form.max_applications_per_day ?? 20} onChange={e => set('max_applications_per_day', parseInt(e.target.value))} />
            </div>
          </div>
        </CardContent>
      </Card>

      <Button onClick={() => saveMut.mutate()} disabled={saveMut.isPending} variant="glow" className="w-full">
        {saveMut.isPending ? 'Saving…' : <><Settings className="h-4 w-4 mr-2" />Save Settings</>}
      </Button>
    </div>
  )
}
