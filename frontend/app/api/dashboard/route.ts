import { NextResponse } from "next/server"
import { apiFetch, ApiError } from "@/lib/api-client"
import { config } from "@/lib/config"
import { getAuthToken } from "@/lib/auth"
import {
  type DashboardSummaryResponse,
  transformDashboardSummaryResponse,
} from "@/lib/types"

export async function GET() {
  try {
    const token = await getAuthToken()

    if (!token) {
      return NextResponse.json({ success: false, message: "Unauthorized" }, { status: 401 })
    }

    const backendSummary = await apiFetch<DashboardSummaryResponse>(
      config.api.endpoints.backend.dashboard.summary,
      {
        method: "GET",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    )

    const summary = transformDashboardSummaryResponse(backendSummary)

    return NextResponse.json({
      success: true,
      data: summary,
    })
  } catch (error) {
    console.error("[Strategos] Get dashboard summary error:", error)

    if (error instanceof ApiError) {
      return NextResponse.json(
        { success: false, message: error.message },
        { status: error.status },
      )
    }

    return NextResponse.json(
      { success: false, message: "Failed to fetch dashboard summary" },
      { status: 500 },
    )
  }
}
