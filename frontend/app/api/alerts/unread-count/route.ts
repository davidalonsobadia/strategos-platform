import { NextResponse } from "next/server"
import { apiFetch, ApiError } from "@/lib/api-client"
import { config } from "@/lib/config"
import { getAuthToken } from "@/lib/auth"

export async function GET() {
  try {
    const token = await getAuthToken()

    if (!token) {
      return NextResponse.json({ success: false, message: "Unauthorized" }, { status: 401 })
    }

    const data = await apiFetch<{ count: number }>(
      config.api.endpoints.backend.alerts.unreadCount,
      {
        method: "GET",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      },
    )

    return NextResponse.json({ success: true, data })
  } catch (error) {
    console.error("[Strategos] Alerts unread-count error:", error)

    if (error instanceof ApiError) {
      return NextResponse.json({ success: false, message: error.message }, { status: error.status })
    }

    return NextResponse.json(
      { success: false, message: "Failed to fetch unread count" },
      { status: 500 },
    )
  }
}
