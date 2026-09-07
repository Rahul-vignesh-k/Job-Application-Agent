import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatSalary(min?: number, max?: number, currency = "USD"): string {
  if (!min && !max) return "—"
  const fmt = (n: number) => {
    if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`
    if (n >= 1_000) return `${(n / 1_000).toFixed(0)}k`
    return n.toString()
  }
  const symbols: Record<string, string> = { USD: "$", INR: "₹", EUR: "€", GBP: "£" }
  const sym = symbols[currency] ?? currency + " "
  if (min && max) return `${sym}${fmt(min)} – ${sym}${fmt(max)}`
  if (min) return `${sym}${fmt(min)}+`
  return `up to ${sym}${fmt(max!)}`
}

export function timeAgo(dateStr: string | null): string {
  if (!dateStr) return "—"
  const diff = (Date.now() - new Date(dateStr).getTime()) / 1000
  if (diff < 60) return "just now"
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
  if (diff < 604800) return `${Math.floor(diff / 86400)}d ago`
  return new Date(dateStr).toLocaleDateString()
}

export function scoreColor(score: number): string {
  if (score >= 85) return "text-emerald-400"
  if (score >= 65) return "text-amber-400"
  return "text-red-400"
}

export function scoreBg(score: number): string {
  if (score >= 85) return "bg-emerald-500/10 border-emerald-500/20 text-emerald-400"
  if (score >= 65) return "bg-amber-500/10 border-amber-500/20 text-amber-400"
  return "bg-red-500/10 border-red-500/20 text-red-400"
}

export function statusConfig(status: string) {
  const map: Record<string, { label: string; color: string; dot: string }> = {
    discovered:     { label: "Discovered",    color: "bg-slate-500/10 text-slate-400 border-slate-500/20",  dot: "bg-slate-400" },
    analyzing:      { label: "Analysing",     color: "bg-blue-500/10 text-blue-400 border-blue-500/20",     dot: "bg-blue-400 animate-pulse" },
    review_required:{ label: "Review Needed", color: "bg-amber-500/10 text-amber-400 border-amber-500/20",  dot: "bg-amber-400" },
    tailoring:      { label: "Tailoring",     color: "bg-purple-500/10 text-purple-400 border-purple-500/20", dot: "bg-purple-400 animate-pulse" },
    ready_to_apply: { label: "Ready",         color: "bg-cyan-500/10 text-cyan-400 border-cyan-500/20",     dot: "bg-cyan-400" },
    applying:       { label: "Applying",      color: "bg-brand-500/10 text-brand-400 border-brand-500/20",  dot: "bg-brand-400 animate-pulse" },
    applied:        { label: "Applied",       color: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20", dot: "bg-emerald-400" },
    waiting_input:  { label: "Input Needed",  color: "bg-orange-500/10 text-orange-400 border-orange-500/20", dot: "bg-orange-400 animate-pulse" },
    failed:         { label: "Failed",        color: "bg-red-500/10 text-red-400 border-red-500/20",        dot: "bg-red-400" },
    skipped:        { label: "Skipped",       color: "bg-slate-500/10 text-slate-400 border-slate-500/20",  dot: "bg-slate-400" },
    interview:      { label: "Interview",     color: "bg-violet-500/10 text-violet-400 border-violet-500/20", dot: "bg-violet-400" },
    rejected:       { label: "Rejected",      color: "bg-red-500/10 text-red-400 border-red-500/20",        dot: "bg-red-400" },
  }
  return map[status] ?? { label: status, color: "bg-muted text-muted-foreground border-border", dot: "bg-muted-foreground" }
}

export function platformIcon(platform: string): string {
  const icons: Record<string, string> = {
    linkedin: "in",
    naukri: "nk",
    indeed: "id",
    glassdoor: "gd",
    manual: "me",
  }
  return icons[platform] ?? "??"
}
