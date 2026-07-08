// Dashboard feature API client (client-side).
// Calls the Next.js route handler under /api/dashboard — never the backend
// directly.
import type { DashboardSummary } from "@/lib/types"

export const dashboardApi = {
  async getSummary(): Promise<{
    success: boolean
    data?: DashboardSummary
    message?: string
  }> {
    const response = await fetch("/api/dashboard")
    return response.json()
  },
}
