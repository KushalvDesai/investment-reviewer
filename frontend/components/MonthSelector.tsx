"use client";

interface MonthSelectorProps {
  months: string[];
  value: string;
  onChange: (month: string) => void;
  label?: string;
  placeholder?: string;
}

export default function MonthSelector({
  months,
  value,
  onChange,
  label = "Month",
  placeholder = "Select a month",
}: MonthSelectorProps) {
  return (
    <div className="flex flex-col gap-1">
      {label && (
        <label className="text-sm font-medium text-gray-400">{label}</label>
      )}
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-100 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
      >
        <option value="" disabled>
          {placeholder}
        </option>
        {months.map((m) => (
          <option key={m} value={m}>
            {m}
          </option>
        ))}
      </select>
    </div>
  );
}
