import { Badge } from "@/components/ui/badge"
import { Card } from "@/components/ui/card"
import { cn } from "@/lib/utils"
import type { Task, TaskPriority } from "@/lib/types"

interface MisTareasProps {
  tasks: Task[]
}

// Format an ISO date (YYYY-MM-DD) as DD/MM/YYYY without timezone drift.
function formatDate(isoDate: string): string {
  const [year, month, day] = isoDate.split("-")
  if (!year || !month || !day) return isoDate
  return `${day}/${month}/${year}`
}

// Priority badge colours mirror the task cards in the mock: Alta red, Media
// amber, Baja grey.
const PRIORITY_BADGE: Record<TaskPriority, string> = {
  Alta: "bg-red-100 text-red-700",
  Media: "bg-amber-100 text-amber-700",
  Baja: "bg-slate-100 text-slate-600",
}

export function MisTareas({ tasks }: MisTareasProps) {
  return (
    <Card className="gap-0 border-slate-200 py-0">
      <h2 className="border-b border-slate-100 px-6 py-5 text-lg font-bold text-slate-900">
        Mis tareas de hoy
      </h2>
      {tasks.length === 0 ? (
        <p className="px-6 py-12 text-center text-sm text-slate-500">
          No tienes tareas para hoy.
        </p>
      ) : (
        <ul className="divide-y divide-slate-100">
          {tasks.map((task) => (
            <li key={task.id} className="flex items-center gap-4 px-6 py-4">
              <div className="min-w-0 flex-1">
                <p className="font-semibold text-slate-900">{task.title}</p>
                <p className="truncate text-sm text-slate-500">
                  {task.project.name} · vence {formatDate(task.dueDate)}
                </p>
              </div>
              <Badge
                variant="secondary"
                className={cn("font-medium", PRIORITY_BADGE[task.priority])}
              >
                {task.priority}
              </Badge>
            </li>
          ))}
        </ul>
      )}
    </Card>
  )
}
