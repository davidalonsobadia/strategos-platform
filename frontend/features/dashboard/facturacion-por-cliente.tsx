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
import type { CustomerBilling } from "@/lib/types"
import { formatEuro } from "./format"

const HEAD_CLASS = "text-xs font-semibold uppercase tracking-wide text-slate-500"

interface FacturacionPorClienteProps {
  rows: CustomerBilling[]
}

// Net billing (invoices minus credit-memo *facturas rectificativas*) per
// customer, highest first. Sourced live from Business Central.
export function FacturacionPorCliente({ rows }: FacturacionPorClienteProps) {
  return (
    <Card className="gap-0 border-slate-200 py-0">
      <h2 className="border-b border-slate-100 px-6 py-5 text-lg font-bold text-slate-900">
        Facturación por cliente
      </h2>
      {rows.length === 0 ? (
        <p className="px-6 py-12 text-center text-sm text-slate-500">
          Sin facturación registrada.
        </p>
      ) : (
        <Table>
          <TableHeader>
            <TableRow className="hover:bg-transparent">
              <TableHead className={cn(HEAD_CLASS, "px-6 py-4")}>Cliente</TableHead>
              <TableHead className={cn(HEAD_CLASS, "px-6 py-4 text-right")}>
                Facturación neta
              </TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows.map((row) => (
              <TableRow key={row.customer_id} className="border-slate-100">
                <TableCell className="px-6 py-4 font-medium text-slate-900">
                  <div className="max-w-xs truncate" title={row.customer_name}>
                    {row.customer_name}
                  </div>
                </TableCell>
                <TableCell className="px-6 py-4 text-right tabular-nums text-slate-700">
                  {formatEuro(row.net_billed)}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </Card>
  )
}
