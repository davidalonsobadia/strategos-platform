import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import { Card } from "@/components/ui/card"
import { getInitials } from "@/lib/navigation"
import { cn } from "@/lib/utils"
import type { Task, TaskPriority } from "@/lib/types"

interface TaskCardProps {
  task: Task
}

// Format an ISO date (YYYY-MM-DD) as DD/MM/YYYY without timezone drift.
function formatDate(isoDate: string): string {
  const [year, month, day] = isoDate.split("-")
  if (!year || !month || !day) return isoDate
  return `${day}/${month}/${year}`
}

// Priority badge colours mirror the task cards in tareas.png: Alta red,
// Media amber, Baja grey.
const PRIORITY_BADGE: Record<TaskPriority, string> = {
  Alta: "bg-red-100 text-red-700",
  Media: "bg-amber-100 text-amber-700",
  Baja: "bg-slate-100 text-slate-600",
}

export function TaskCard({ task }: TaskCardProps) {
  return (
    <Card className="gap-4 border-slate-200 px-5 py-5">
      <div className="min-w-0">
        <h3 className="text-base font-bold text-slate-900">{task.title}</h3>
        <p className="truncate text-sm text-slate-500">{task.project.name}</p>
      </div>

      <div className="flex items-center justify-between gap-2">
        <Badge
          variant="secondary"
          className={cn("font-medium", PRIORITY_BADGE[task.priority])}
        >
          {task.priority}
        </Badge>
        <span className="text-sm text-slate-500">{formatDate(task.dueDate)}</span>
      </div>

      <div className="flex items-center gap-2 border-t border-slate-100 pt-4">
        <Avatar className="size-7">
          <AvatarFallback className="bg-[#0e1729] text-xs font-semibold text-white">
            {getInitials(task.assignee.name)}
          </AvatarFallback>
        </Avatar>
        <span className="truncate text-sm text-slate-700">{task.assignee.name}</span>
      </div>
    </Card>
  )
}
