"use client";

interface StatCardProps {
  label: string;
  value: number;
  variant?: "income" | "expense" | "pnl" | "neutral";
}

function formatCurrency(value: number): string {
  const abs = Math.abs(value);
  const formatted = new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(abs);
  return value < 0 ? `-${formatted}` : formatted;
}

const variantStyles: Record<string, string> = {
  income: "border-emerald-700 bg-emerald-950/40",
  expense: "border-rose-700 bg-rose-950/40",
  pnl: "border-indigo-700 bg-indigo-950/40",
  neutral: "border-gray-700 bg-gray-800",
};

const valueStyles: Record<string, string> = {
  income: "text-emerald-400",
  expense: "text-rose-400",
  pnl: "text-indigo-400",
  neutral: "text-gray-100",
};

export default function StatCard({
  label,
  value,
  variant = "neutral",
}: StatCardProps) {
  const isNegativePnl = variant === "pnl" && value < 0;
  const effectiveVariant = isNegativePnl ? "expense" : variant;

  return (
    <div
      className={`rounded-xl border p-5 ${variantStyles[effectiveVariant]}`}
    >
      <p className="mb-1 text-xs font-medium uppercase tracking-wider text-gray-500">
        {label}
      </p>
      <p className={`text-2xl font-bold tabular-nums ${valueStyles[effectiveVariant]}`}>
        {formatCurrency(value)}
      </p>
    </div>
  );
}
