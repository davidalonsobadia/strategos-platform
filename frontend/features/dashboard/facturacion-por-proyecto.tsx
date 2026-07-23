import { Card } from "@/components/ui/card"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { cn } from "@/lib/utils"
import type { ProjectBilling } from "@/lib/types"
import { formatEuro, formatHours } from "./format"

const HEAD_CLASS = "text-xs font-semibold uppercase tracking-wide text-slate-500"
// Right-aligned, tabular figures so decimals line up and widths don't jump.
const NUM_CLASS = "px-6 py-4 text-right tabular-nums"

interface FacturacionPorProyectoProps {
  rows: ProjectBilling[]
}

// Billing, usage cost and logged hours per project, highest billing first.
// Billing = invoices minus credit memos on the project's lines; cost = job
// ledger usage cost; hours = time-sheet quantity. Sourced live from BC.
export function FacturacionPorProyecto({ rows }: FacturacionPorProyectoProps) {
  return (
    <Card className="gap-0 border-slate-200 py-0">
      <h2 className="border-b border-slate-100 px-6 py-5 text-lg font-bold text-slate-900">
        Facturación y costes por proyecto
      </h2>
      {rows.length === 0 ? (
        <p className="px-6 py-12 text-center text-sm text-slate-500">
          Sin datos de proyecto.
        </p>
      ) : (
        <Table>
          <TableHeader>
            <TableRow className="hover:bg-transparent">
              <TableHead className={cn(HEAD_CLASS, "px-6 py-4")}>Proyecto</TableHead>
              <TableHead className={cn(HEAD_CLASS, "px-6 py-4 text-right")}>
                Facturación
              </TableHead>
              <TableHead className={cn(HEAD_CLASS, "px-6 py-4 text-right")}>
                Coste
              </TableHead>
              <TableHead className={cn(HEAD_CLASS, "px-6 py-4 text-right")}>
                Horas
              </TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows.map((row) => (
              <TableRow key={row.project_id} className="border-slate-100">
                <TableCell className="px-6 py-4">
                  {/* Truncate long names so they never squeeze the numeric
                      columns; title keeps the full name on hover and the id
                      subline aids quick identification. */}
                  <div
                    className="max-w-[16rem] truncate font-medium text-slate-900"
                    title={row.project_name}
                  >
                    {row.project_name}
                  </div>
                  <div className="text-xs text-slate-400">{row.project_id}</div>
                </TableCell>
                <TableCell className={cn(NUM_CLASS, "text-slate-700")}>
                  {formatEuro(row.billed)}
                </TableCell>
                <TableCell className={cn(NUM_CLASS, "text-slate-700")}>
                  {formatEuro(row.cost)}
                </TableCell>
                <TableCell className={cn(NUM_CLASS, "text-slate-500")}>
                  {formatHours(row.hours)}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </Card>
  )
}
