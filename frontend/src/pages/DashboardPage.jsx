import { Routes, Route, Navigate } from 'react-router-dom'
import DashboardLayout from '../components/DashboardLayout'
import DashboardSummary from './DashboardSummary'
import NewRequestPage from './NewRequestPage'
import MyRequestsPage from './MyRequestsPage'
import AllRequestsPage from './AllRequestsPage'
import PosmManagementPage from './PosmManagementPage'
import UserManagementPage from './UserManagementPage'
import DealerManagementPage from './DealerManagementPage'
import BulkDealerImportPage from './BulkDealerImportPage'
import WorkPlanPage from './WorkPlanPage'
import ReportsPage from './ReportsPage'
import PlannedWorkPage from './PlannedWorkPage'
import AuditLogPage from './AuditLogPage'
import ReportManagementPage from './ReportManagementPage'

function DashboardPage() {
  return (
    <DashboardLayout>
      <Routes>
        <Route path="/" element={<DashboardSummary />} />
        <Route path="new-request" element={<NewRequestPage />} />
        <Route path="my-requests" element={<MyRequestsPage />} />
        <Route path="all-requests" element={<AllRequestsPage />} />
        <Route path="posm-management" element={<PosmManagementPage />} />
        <Route path="user-management" element={<UserManagementPage />} />
        <Route path="dealer-management" element={<DealerManagementPage />} />
        <Route path="bulk-import" element={<BulkDealerImportPage />} />
        <Route path="work-plan" element={<WorkPlanPage />} />
        <Route path="planned-work" element={<PlannedWorkPage />} />
        <Route path="reports" element={<ReportsPage />} />
        <Route path="audit-logs" element={<AuditLogPage />} />
        <Route path="report-management" element={<ReportManagementPage />} />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </DashboardLayout>
  )
}

export default DashboardPage
