import { ComingSoon } from "@/components/coming-soon"

// The legacy TaskFlow lists dashboard was removed with the lists frontend
// (issue #16). The dedicated Dashboard page lands in its own task; until then
// this keeps the `/dashboard` nav route alive without depending on removed
// modules.
export default function DashboardPage() {
  return <ComingSoon title="Dashboard" />
}
