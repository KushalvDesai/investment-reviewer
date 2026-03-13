"use client";

import { useEffect, useState } from "react";

import InsightsList from "@/components/InsightsList";
import MonthSelector from "@/components/MonthSelector";
import StatCard from "@/components/StatCard";
import {
  analyzeMonth,
  listMonths,
  type SingleMonthAnalysis,
} from "@/lib/api";

export default function DashboardPage() {
  const [months, setMonths] = useState<string[]>([]);
  const [selectedMonth, setSelectedMonth] = useState("");
  const [question, setQuestion] = useState("Summarize my income, expenses, and net profit/loss.");
  const [analysis, setAnalysis] = useState<SingleMonthAnalysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    listMonths()
      .then((m) => {
        setMonths(m);
        if (m.length > 0) setSelectedMonth(m[0]);
      })
      .catch(() => setError("Failed to load months from Pinecone."));
  }, []);

  async function handleAnalyze() {
    if (!selectedMonth) return;
    setLoading(true);
    setError("");
    setAnalysis(null);
    try {
      const result = await analyzeMonth(selectedMonth, question);
      setAnalysis(result);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Analysis failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-white">Dashboard</h1>
        <p className="mt-1 text-sm text-gray-500">
          Analyze a single month's financial statement.
        </p>
      </div>

      {months.length === 0 ? (
        <div className="rounded-xl border border-gray-700 bg-gray-800/40 p-8 text-center">
          <p className="text-gray-400">
            No statements uploaded yet.{" "}
            <a href="/upload" className="text-indigo-400 underline">
              Upload a PDF
            </a>{" "}
            to get started.
          </p>
        </div>
      ) : (
        <>
          <div className="flex flex-wrap items-end gap-4">
            <MonthSelector
              months={months}
              value={selectedMonth}
              onChange={setSelectedMonth}
              label="Statement Month"
            />
            <div className="flex flex-1 flex-col gap-1 min-w-[260px]">
              <label className="text-sm font-medium text-gray-400">Question</label>
              <input
                type="text"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                className="rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-100 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
            </div>
            <button
              onClick={handleAnalyze}
              disabled={loading || !selectedMonth}
              className="rounded-lg bg-indigo-600 px-5 py-2 text-sm font-semibold text-white transition hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {loading ? "Analyzing…" : "Analyze"}
            </button>
          </div>

          {error && (
            <p className="rounded-lg border border-rose-700 bg-rose-950/30 px-4 py-3 text-sm text-rose-400">
              {error}
            </p>
          )}

          {analysis && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                <StatCard
                  label="Total Income"
                  value={analysis.total_income}
                  variant="income"
                />
                <StatCard
                  label="Total Expenses"
                  value={analysis.total_expenses}
                  variant="expense"
                />
                <StatCard
                  label="Net P&L"
                  value={analysis.net_pnl}
                  variant="pnl"
                />
              </div>

              <div className="rounded-xl border border-gray-700 bg-gray-800/40 p-5">
                <h2 className="mb-2 text-sm font-semibold text-gray-300">Summary</h2>
                <p className="text-sm leading-relaxed text-gray-400">
                  {analysis.summary}
                </p>
              </div>

              {analysis.key_transactions.length > 0 && (
                <div className="rounded-xl border border-gray-700 bg-gray-800/40 p-5">
                  <h2 className="mb-3 text-sm font-semibold text-gray-300">
                    Key Transactions
                  </h2>
                  <div className="space-y-2">
                    {analysis.key_transactions.map((tx, i) => (
                      <div
                        key={i}
                        className="flex justify-between text-sm text-gray-400"
                      >
                        <span>{tx.description}</span>
                        <span
                          className={
                            tx.amount >= 0 ? "text-emerald-400" : "text-rose-400"
                          }
                        >
                          {tx.amount >= 0 ? "+" : ""}
                          {tx.amount.toLocaleString("en-US", {
                            style: "currency",
                            currency: "USD",
                          })}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="rounded-xl border border-gray-700 bg-gray-800/40 p-5">
                <InsightsList insights={analysis.insights} />
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
