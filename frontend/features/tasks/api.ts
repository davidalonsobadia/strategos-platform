// Tasks feature API client (client-side).
// Calls the Next.js route handler under /api/tasks — never the backend directly.
import type { Task, TaskStatus } from "@/lib/types"

export interface GetTasksParams {
  status?: TaskStatus
  projectId?: string
  assigneeId?: string
}

export const tasksApi = {
  async getTasks(
    params: GetTasksParams = {},
  ): Promise<{ success: boolean; data?: Task[]; message?: string }> {
    const query = new URLSearchParams()
    if (params.status) query.set("status", params.status)
    if (params.projectId) query.set("project_id", params.projectId)
    if (params.assigneeId) query.set("assignee_id", params.assigneeId)
    const queryString = query.toString()

    const response = await fetch(`/api/tasks${queryString ? `?${queryString}` : ""}`)
    return response.json()
  },
}
