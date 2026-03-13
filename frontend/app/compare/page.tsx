"use client";

import { useEffect, useState } from "react";

import CompareTable from "@/components/CompareTable";
import InsightsList from "@/components/InsightsList";
import MonthSelector from "@/components/MonthSelector";
import { compareMonths, listMonths, type MonthComparisonResult } from "@/lib/api";

export default function ComparePage() {
  const [months, setMonths] = useState<string[]>([]);
  const [currentMonth, setCurrentMonth] = useState("");
  const [previousMonth, setPreviousMonth] = useState("");
  const [result, setResult] = useState<MonthComparisonResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    listMonths()
      .then((m) => {
        setMonths(m);
        if (m.length >= 1) setCurrentMonth(m[0]);
        if (m.length >= 2) setPreviousMonth(m[1]);
      })
      .catch(() => setError("Failed to load months."));
  }, []);

  async function handleCompare() {
    if (!currentMonth || !previousMonth) return;
    if (currentMonth === previousMonth) {
      setError("Please select two different months.");
      return;
    }
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const data = await compareMonths(currentMonth, previousMonth);
      setResult(data);
    } catch (err: unknown) {
      setError(
        err instanceof Error ? err.message : "Comparison failed."
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-white">Month Comparison</h1>
        <p className="mt-1 text-sm text-gray-500">
          Side-by-side month-over-month profit &amp; loss analysis.
        </p>
      </div>

      {months.length < 2 ? (
        <div className="rounded-xl border border-gray-700 bg-gray-800/40 p-8 text-center">
          <p className="text-gray-400">
            You need at least two months indexed to compare.{" "}
            <a href="/upload" className="text-indigo-400 underline">
              Upload more statements.
            </a>
          </p>
        </div>
      ) : (
        <>
          <div className="flex flex-wrap items-end gap-4">
            <MonthSelector
              months={months}
              value={currentMonth}
              onChange={setCurrentMonth}
              label="Current Month"
            />
            <MonthSelector
              months={months}
              value={previousMonth}
              onChange={setPreviousMonth}
              label="Previous Month"
            />
            <button
              onClick={handleCompare}
              disabled={loading || !currentMonth || !previousMonth}
              className="rounded-lg bg-indigo-600 px-5 py-2 text-sm font-semibold text-white transition hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {loading ? "Comparing…" : "Compare"}
            </button>
          </div>

          {error && (
            <p className="rounded-lg border border-rose-700 bg-rose-950/30 px-4 py-3 text-sm text-rose-400">
              {error}
            </p>
          )}

          {result && (
            <div className="space-y-6">
              <CompareTable data={result} />

              <div className="rounded-xl border border-gray-700 bg-gray-800/40 p-5">
                <InsightsList
                  highlights={result.highlights}
                  warnings={result.warnings}
                  recommendations={result.recommendations}
                />
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
