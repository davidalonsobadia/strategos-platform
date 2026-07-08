"use client"

import { useEffect, useState } from "react"

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { tasksApi } from "@/features/tasks/api"
import { TasksBoard } from "@/features/tasks/tasks-board"
import type { Task, TaskStatus } from "@/lib/types"

const ALL = "all"

const STATUS_OPTIONS: TaskStatus[] = ["Pendiente", "En curso", "Hecho"]

export default function TareasPage() {
  const [status, setStatus] = useState<string>(ALL)
  const [tasks, setTasks] = useState<Task[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let active = true

    const loadTasks = async () => {
      setLoading(true)
      try {
        const result = await tasksApi.getTasks({
          status: status === ALL ? undefined : (status as TaskStatus),
        })
        if (!active) return
        setTasks(result.success && result.data ? result.data : [])
      } catch (error) {
        console.error("[Strategos] Load tasks error:", error)
        if (active) setTasks([])
      } finally {
        if (active) setLoading(false)
      }
    }

    loadTasks()
    return () => {
      active = false
    }
  }, [status])

  return (
    <div className="px-8 py-8">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-bold text-slate-900">Tareas</h1>
        <Select value={status} onValueChange={setStatus}>
          <SelectTrigger className="h-11 bg-white sm:w-48">
            <SelectValue placeholder="Todos" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={ALL}>Todos</SelectItem>
            {STATUS_OPTIONS.map((option) => (
              <SelectItem key={option} value={option}>
                {option}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="mt-6">
        <TasksBoard tasks={tasks} loading={loading} />
      </div>
    </div>
  )
}
