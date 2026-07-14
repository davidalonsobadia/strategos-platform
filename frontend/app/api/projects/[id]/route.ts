import { type NextRequest, NextResponse } from "next/server"
import { apiFetch, ApiError } from "@/lib/api-client"
import { config } from "@/lib/config"
import { getAuthToken } from "@/lib/auth"
import { type ProjectResponse, transformProjectResponse } from "@/lib/types"

export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  try {
    const token = await getAuthToken()

    if (!token) {
      return NextResponse.json({ success: false, message: "Unauthorized" }, { status: 401 })
    }

    const { id } = await params

    const backendProject = await apiFetch<ProjectResponse>(
      config.api.endpoints.backend.projects.byId(id),
      {
        method: "GET",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    )

    return NextResponse.json({
      success: true,
      data: transformProjectResponse(backendProject),
    })
  } catch (error) {
    console.error("[Strategos] Get project error:", error)

    if (error instanceof ApiError) {
      return NextResponse.json(
        { success: false, message: error.message },
        { status: error.status },
      )
    }

    return NextResponse.json({ success: false, message: "Failed to fetch project" }, { status: 500 })
  }
}
