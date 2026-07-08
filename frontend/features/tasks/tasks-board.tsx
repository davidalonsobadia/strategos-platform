import { TaskCard } from "./task-card"
import type { Task, TaskStatus } from "@/lib/types"

interface TasksBoardProps {
  tasks: Task[]
  loading: boolean
}

// The three board columns, in the order shown in tareas.png.
const COLUMNS: TaskStatus[] = ["Pendiente", "En curso", "Hecho"]

export function TasksBoard({ tasks, loading }: TasksBoardProps) {
  if (loading) {
    return (
      <div className="flex min-h-[240px] items-center justify-center rounded-lg border border-dashed border-slate-300 bg-white">
        <p className="text-sm text-slate-500">Cargando tareas...</p>
      </div>
    )
  }

  // Group tasks into their board column, preserving backend order within each.
  const byStatus: Record<TaskStatus, Task[]> = {
    Pendiente: [],
    "En curso": [],
    Hecho: [],
  }
  for (const task of tasks) {
    byStatus[task.status]?.push(task)
  }

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
      {COLUMNS.map((status) => {
        const columnTasks = byStatus[status]
        return (
          <section key={status} className="rounded-lg bg-slate-100/60 p-4">
            <h2 className="mb-4 px-1 text-sm font-semibold text-slate-500">
              {status} · {columnTasks.length}
            </h2>
            <div className="space-y-4">
              {columnTasks.length === 0 ? (
                <p className="px-1 text-sm text-slate-400">Sin tareas.</p>
              ) : (
                columnTasks.map((task) => <TaskCard key={task.id} task={task} />)
              )}
            </div>
          </section>
        )
      })}
    </div>
  )
}
