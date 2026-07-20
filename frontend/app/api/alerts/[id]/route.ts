import { type NextRequest, NextResponse } from "next/server"
import { apiFetch, ApiError } from "@/lib/api-client"
import { config } from "@/lib/config"
import { getAuthToken } from "@/lib/auth"
import type { Alert } from "@/features/alerts/api"

export async function PATCH(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  try {
    const token = await getAuthToken()

    if (!token) {
      return NextResponse.json({ success: false, message: "Unauthorized" }, { status: 401 })
    }

    const { id } = await params
    const body = await request.json()

    const data = await apiFetch<Alert>(
      config.api.endpoints.backend.alerts.byId(id),
      {
        method: "PATCH",
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ status: body.status }),
      },
    )

    return NextResponse.json({ success: true, data })
  } catch (error) {
    console.error("[Strategos] Update alert error:", error)

    if (error instanceof ApiError) {
      return NextResponse.json({ success: false, message: error.message }, { status: error.status })
    }

    return NextResponse.json(
      { success: false, message: "Failed to update alert" },
      { status: 500 },
    )
  }
}
