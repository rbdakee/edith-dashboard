import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AppLayout } from '@/components/layout/AppLayout'
import { LoginPage } from '@/pages/LoginPage'
import { SetupPage } from '@/pages/SetupPage'
import { OverviewPage } from '@/pages/OverviewPage'
import { KanbanPage } from '@/pages/KanbanPage'
import { TasksPage } from '@/pages/TasksPage'
import { EventsPage } from '@/pages/EventsPage'
import { SessionsPage } from '@/pages/SessionsPage'
import { AgentsPage } from '@/pages/AgentsPage'
import { FilesPage } from '@/pages/FilesPage'
import { CommentsPage } from '@/pages/CommentsPage'
import { TimelinePage } from '@/pages/TimelinePage'
import { SettingsPage } from '@/pages/SettingsPage'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/setup" element={<SetupPage />} />
        <Route path="/" element={<AppLayout />}>
          <Route index element={<Navigate to="/overview" replace />} />
          <Route path="overview" element={<OverviewPage />} />
          <Route path="kanban" element={<KanbanPage />} />
          <Route path="tasks" element={<TasksPage />} />
          <Route path="events" element={<EventsPage />} />
          <Route path="sessions" element={<SessionsPage />} />
          <Route path="agents" element={<AgentsPage />} />
          <Route path="files" element={<FilesPage />} />
          <Route path="comments" element={<CommentsPage />} />
          <Route path="timeline" element={<TimelinePage />} />
          <Route path="settings" element={<SettingsPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
