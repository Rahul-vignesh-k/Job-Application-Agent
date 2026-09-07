import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Layout } from '@/components/layout/Layout'
import { Dashboard } from '@/pages/Dashboard'
import { JobQueue } from '@/pages/JobQueue'
import { JobDetail } from '@/pages/JobDetail'
import { MatchReport } from '@/pages/MatchReport'
import { ResumePreview } from '@/pages/ResumePreview'
import { ManualInput } from '@/pages/ManualInput'
import { History } from '@/pages/History'
import { SettingsPage } from '@/pages/SettingsPage'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/jobs" element={<JobQueue />} />
          <Route path="/jobs/:id" element={<JobDetail />} />
          <Route path="/match" element={<MatchReport />} />
          <Route path="/resumes" element={<ResumePreview />} />
          <Route path="/preview" element={<ResumePreview />} />
          <Route path="/input" element={<ManualInput />} />
          <Route path="/history" element={<History />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
