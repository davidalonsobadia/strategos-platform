import { type NextRequest, NextResponse } from "next/server"
import { apiFetch, ApiError } from "@/lib/api-client"
import { config } from "@/lib/config"
import { getAuthToken } from "@/lib/auth"
import { type CustomerPageResponse, transformCustomerPageResponse } from "@/lib/types"

export async function GET(request: NextRequest) {
  try {
    const token = await getAuthToken()

    if (!token) {
      return NextResponse.json({ success: false, message: "Unauthorized" }, { status: 401 })
    }

    const { searchParams } = new URL(request.url)
    const search = searchParams.get("search")
    const status = searchParams.get("status")
    const cursor = searchParams.get("cursor")

    // Forward the optional search/status/cursor params to the backend
    // (server-side filtering and pagination).
    const query = new URLSearchParams()
    if (search) query.set("search", search)
    if (status) query.set("status", status)
    if (cursor) query.set("cursor", cursor)
    const queryString = query.toString()

    const backendPage = await apiFetch<CustomerPageResponse>(
      `${config.api.endpoints.backend.customers.base}${queryString ? `?${queryString}` : ""}`,
      {
        method: "GET",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    )

    return NextResponse.json({
      success: true,
      data: transformCustomerPageResponse(backendPage),
    })
  } catch (error) {
    console.error("[Strategos] Get customers error:", error)

    if (error instanceof ApiError) {
      return NextResponse.json(
        { success: false, message: error.message },
        { status: error.status },
      )
    }

    return NextResponse.json({ success: false, message: "Failed to fetch customers" }, { status: 500 })
  }
}
