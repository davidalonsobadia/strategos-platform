import { type NextRequest, NextResponse } from "next/server"
import { apiFetch, ApiError } from "@/lib/api-client"
import { config } from "@/lib/config"
import { getAuthToken } from "@/lib/auth"
import { type TaskResponse, transformTaskResponse } from "@/lib/types"

export async function GET(request: NextRequest) {
  try {
    const token = await getAuthToken()

    if (!token) {
      return NextResponse.json({ success: false, message: "Unauthorized" }, { status: 401 })
    }

    const { searchParams } = new URL(request.url)
    const status = searchParams.get("status")
    const projectId = searchParams.get("project_id")
    const assigneeId = searchParams.get("assignee_id")

    // Forward the optional filters to the backend (server-side filtering).
    const query = new URLSearchParams()
    if (status) query.set("status", status)
    if (projectId) query.set("project_id", projectId)
    if (assigneeId) query.set("assignee_id", assigneeId)
    const queryString = query.toString()

    const backendTasks = await apiFetch<TaskResponse[]>(
      `${config.api.endpoints.backend.tasks.base}${queryString ? `?${queryString}` : ""}`,
      {
        method: "GET",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    )

    const tasks = backendTasks.map(transformTaskResponse)

    return NextResponse.json({
      success: true,
      data: tasks,
    })
  } catch (error) {
    console.error("[Strategos] Get tasks error:", error)

    if (error instanceof ApiError) {
      return NextResponse.json(
        { success: false, message: error.message },
        { status: error.status },
      )
    }

    return NextResponse.json({ success: false, message: "Failed to fetch tasks" }, { status: 500 })
  }
}
