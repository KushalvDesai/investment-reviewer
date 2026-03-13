"use client";

import type { ChangeMetric, MonthComparisonResult } from "@/lib/api";

interface CompareTableProps {
  data: MonthComparisonResult;
}

function formatCurrency(value: number): string {
  const abs = Math.abs(value);
  const s = new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
  }).format(abs);
  return value < 0 ? `-${s}` : s;
}

function DirectionBadge({ metric }: { metric: ChangeMetric }) {
  if (metric.direction === "up") {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-emerald-900/50 px-2 py-0.5 text-xs font-medium text-emerald-400">
        ▲ {metric.percent.toFixed(1)}%
      </span>
    );
  }
  if (metric.direction === "down") {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-rose-900/50 px-2 py-0.5 text-xs font-medium text-rose-400">
        ▼ {metric.percent.toFixed(1)}%
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-gray-800 px-2 py-0.5 text-xs font-medium text-gray-400">
      — 0%
    </span>
  );
}

const rows = [
  { key: "income_change" as const, label: "Income" },
  { key: "expense_change" as const, label: "Expenses" },
  { key: "net_pnl_change" as const, label: "Net P&L" },
];

export default function CompareTable({ data }: CompareTableProps) {
  return (
    <div className="overflow-hidden rounded-xl border border-gray-700">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-gray-700 bg-gray-800/60">
            <th className="px-4 py-3 text-left font-medium text-gray-400">
              Metric
            </th>
            <th className="px-4 py-3 text-right font-medium text-gray-400">
              {data.previous_month}
            </th>
            <th className="px-4 py-3 text-right font-medium text-gray-400">
              {data.current_month}
            </th>
            <th className="px-4 py-3 text-right font-medium text-gray-400">
              Change
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-800">
          {rows.map(({ key, label }) => {
            const metric = data[key];
            return (
              <tr key={key} className="hover:bg-gray-800/30 transition-colors">
                <td className="px-4 py-3 font-medium text-gray-200">{label}</td>
                <td className="px-4 py-3 text-right tabular-nums text-gray-300">
                  —
                </td>
                <td className="px-4 py-3 text-right tabular-nums text-gray-100">
                  {formatCurrency(metric.amount)}
                </td>
                <td className="px-4 py-3 text-right">
                  <DirectionBadge metric={metric} />
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
