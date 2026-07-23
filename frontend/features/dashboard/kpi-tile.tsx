import { Card } from "@/components/ui/card"
import { cn } from "@/lib/utils"

interface KpiTileProps {
  // Small label above the number (e.g. "Proyectos activos").
  title: string
  // The headline figure — a raw count, or a pre-formatted string (e.g. a euro
  // amount) for the financial tiles.
  value: number | string
  // Muted sublabel below the number (e.g. "de 12 totales").
  sublabel: string
  // Amber sublabel for the "Obligaciones próximas" tile in dashboard.png.
  accent?: boolean
}

export function KpiTile({ title, value, sublabel, accent = false }: KpiTileProps) {
  return (
    <Card className="gap-3 border-slate-200 px-6 py-5">
      <p className="text-sm font-medium text-slate-500">{title}</p>
      <p className="text-4xl font-bold text-slate-900">{value}</p>
      <p className={cn("text-sm", accent ? "text-amber-600" : "text-slate-500")}>
        {sublabel}
      </p>
    </Card>
  )
}
