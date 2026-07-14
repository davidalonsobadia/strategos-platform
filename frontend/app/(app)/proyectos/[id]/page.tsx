"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { useParams } from "next/navigation"

import { Badge } from "@/components/ui/badge"
import { Card } from "@/components/ui/card"
import { ObligationsTable } from "@/features/obligations/obligations-table"
import { obligationsApi } from "@/features/obligations/api"
import { projectsApi } from "@/features/projects/api"
import { TaskCard } from "@/features/tasks/task-card"
import { tasksApi } from "@/features/tasks/api"
import { cn } from "@/lib/utils"
import type { Project, ProjectObligation, Task } from "@/lib/types"

// Format an ISO date (YYYY-MM-DD) as DD/MM/YYYY without timezone drift.
function formatDate(isoDate: string | null | undefined): string {
  if (!isoDate) return "—"
  const [year, month, day] = isoDate.split("-")
  if (!year || !month || !day) return isoDate
  return `${day}/${month}/${year}`
}

// A single label/value row in the General fitxa grid.
function Field({
  label,
  children,
}: {
  label: string
  children: React.ReactNode
}) {
  return (
    <div className="flex flex-col gap-1">
      <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">
        {label}
      </span>
      <span className="text-sm text-slate-900">{children}</span>
    </div>
  )
}

export default function ProyectoDetailPage() {
  const params = useParams<{ id: string }>()
  const id = params.id

  const [project, setProject] = useState<Project | null>(null)
  const [obligations, setObligations] = useState<ProjectObligation[]>([])
  const [tasks, setTasks] = useState<Task[]>([])
  const [loadingProject, setLoadingProject] = useState(true)
  const [loadingObligations, setLoadingObligations] = useState(true)
  const [loadingTasks, setLoadingTasks] = useState(true)
  const [notFound, setNotFound] = useState(false)

  useEffect(() => {
    if (!id) return
    let active = true

    const loadProject = async () => {
      setLoadingProject(true)
      setNotFound(false)
      try {
        const result = await projectsApi.getProject(id)
        if (!active) return
        if (result.success && result.data) {
          setProject(result.data)
        } else {
          setProject(null)
          setNotFound(true)
        }
      } catch (error) {
        console.error("[Strategos] Load project error:", error)
        if (active) {
          setProject(null)
          setNotFound(true)
        }
      } finally {
        if (active) setLoadingProject(false)
      }
    }

    const loadObligations = async () => {
      setLoadingObligations(true)
      try {
        const result = await obligationsApi.getObligations({ projectId: id })
        if (!active) return
        setObligations(result.success && result.data ? result.data : [])
      } catch (error) {
        console.error("[Strategos] Load project obligations error:", error)
        if (active) setObligations([])
      } finally {
        if (active) setLoadingObligations(false)
      }
    }

    const loadTasks = async () => {
      setLoadingTasks(true)
      try {
        const result = await tasksApi.getTasks({ projectId: id })
        if (!active) return
        setTasks(result.success && result.data ? result.data : [])
      } catch (error) {
        console.error("[Strategos] Load project tasks error:", error)
        if (active) setTasks([])
      } finally {
        if (active) setLoadingTasks(false)
      }
    }

    loadProject()
    loadObligations()
    loadTasks()

    return () => {
      active = false
    }
  }, [id])

  if (loadingProject) {
    return (
      <div className="px-8 py-8">
        <div className="rounded-lg border border-slate-200 bg-white px-6 py-12 text-center text-sm text-slate-500">
          Cargando proyecto...
        </div>
      </div>
    )
  }

  if (notFound || !project) {
    return (
      <div className="px-8 py-8">
        <div className="rounded-lg border border-slate-200 bg-white px-6 py-12 text-center">
          <p className="text-sm text-slate-500">No se ha encontrado el proyecto.</p>
          <Link
            href="/proyectos"
            className="mt-4 inline-block text-sm font-semibold text-slate-900 underline"
          >
            Volver a Proyectos
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="px-8 py-8">
      <Link href="/proyectos" className="text-sm text-slate-500 hover:text-slate-900">
        ← Proyectos
      </Link>

      <div className="mt-3 flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <h1 className="text-2xl font-bold text-slate-900">{project.name}</h1>
          <Link
            href={`/clientes/${project.customer.id}`}
            className="text-sm text-slate-500 hover:text-slate-900 hover:underline"
          >
            {project.customer.name}
          </Link>
        </div>
        <Badge
          variant="secondary"
          className={cn(
            "shrink-0 font-medium",
            project.status === "Activo"
              ? "bg-green-100 text-green-700"
              : "bg-slate-100 text-slate-500",
          )}
        >
          {project.status}
        </Badge>
      </div>

      <Card className="mt-6 border-slate-200 px-6 py-6">
        <h2 className="text-lg font-bold text-slate-900">General</h2>
        <div className="mt-4 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
          <Field label="Nombre">{project.name}</Field>
          <Field label="Cliente">
            <Link
              href={`/clientes/${project.customer.id}`}
              className="text-slate-900 hover:underline"
            >
              {project.customer.name}
            </Link>
          </Field>
          <Field label="Tipo de proyecto">{project.projectType || "—"}</Field>
          <Field label="Tipo de entidad">{project.entityType || "—"}</Field>
          <Field label="Responsable">{project.responsible}</Field>
          <Field label="Técnico">{project.technician}</Field>
          <Field label="Certificado">
            {project.hasCertificate == null
              ? "—"
              : project.hasCertificate
                ? `Sí${project.certificateExpiry ? ` · ${formatDate(project.certificateExpiry)}` : ""}`
                : "No"}
          </Field>
          <Field label="Fecha de presentación">{formatDate(project.filingDate)}</Field>
          <Field label="Estado">{project.status}</Field>
        </div>
      </Card>

      <section className="mt-8">
        <h2 className="text-lg font-bold text-slate-900">Obligaciones</h2>
        <div className="mt-4">
          <ObligationsTable obligations={obligations} loading={loadingObligations} />
        </div>
      </section>

      <section className="mt-8">
        <h2 className="text-lg font-bold text-slate-900">Tareas</h2>
        <div className="mt-4">
          {loadingTasks ? (
            <div className="rounded-lg border border-slate-200 bg-white px-6 py-12 text-center text-sm text-slate-500">
              Cargando tareas...
            </div>
          ) : tasks.length === 0 ? (
            <div className="rounded-lg border border-slate-200 bg-white px-6 py-12 text-center text-sm text-slate-500">
              No se han encontrado tareas.
            </div>
          ) : (
            <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
              {tasks.map((task) => (
                <TaskCard key={task.id} task={task} />
              ))}
            </div>
          )}
        </div>
      </section>
    </div>
  )
}
