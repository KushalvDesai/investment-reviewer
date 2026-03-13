"use client";

import { useEffect, useState } from "react";

import { askQuestion, listMonths, type AskResponse } from "@/lib/api";

export default function AskPage() {
  const [months, setMonths] = useState<string[]>([]);
  const [selectedMonths, setSelectedMonths] = useState<Set<string>>(new Set());
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState<AskResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    listMonths()
      .then((m) => {
        setMonths(m);
        setSelectedMonths(new Set(m));
      })
      .catch(() => setError("Failed to load months."));
  }, []);

  function toggleMonth(m: string) {
    setSelectedMonths((prev) => {
      const next = new Set(prev);
      if (next.has(m)) {
        next.delete(m);
      } else {
        next.add(m);
      }
      return next;
    });
  }

  async function handleAsk(e: React.FormEvent) {
    e.preventDefault();
    if (!question.trim() || selectedMonths.size === 0) return;
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const data = await askQuestion(question, Array.from(selectedMonths));
      setResult(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Query failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-white">Ask a Question</h1>
        <p className="mt-1 text-sm text-gray-500">
          Ask any question across one or more months using semantic search + LLM.
        </p>
      </div>

      <form onSubmit={handleAsk} className="space-y-5">
        {months.length > 0 && (
          <div>
            <label className="mb-2 block text-sm font-medium text-gray-400">
              Select Months
            </label>
            <div className="flex flex-wrap gap-2">
              {months.map((m) => (
                <button
                  key={m}
                  type="button"
                  onClick={() => toggleMonth(m)}
                  className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
                    selectedMonths.has(m)
                      ? "bg-indigo-600 text-white"
                      : "bg-gray-800 text-gray-400 hover:bg-gray-700"
                  }`}
                >
                  {m}
                </button>
              ))}
            </div>
            {selectedMonths.size === 0 && (
              <p className="mt-1 text-xs text-rose-400">
                Select at least one month.
              </p>
            )}
          </div>
        )}

        <div>
          <label className="mb-1 block text-sm font-medium text-gray-400">
            Your Question
          </label>
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            rows={3}
            placeholder="e.g. Which month had the highest grocery spending?"
            className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-100 placeholder-gray-600 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 resize-none"
          />
        </div>

        {error && (
          <p className="rounded-lg border border-rose-700 bg-rose-950/30 px-4 py-3 text-sm text-rose-400">
            {error}
          </p>
        )}

        <button
          type="submit"
          disabled={loading || !question.trim() || selectedMonths.size === 0}
          className="rounded-lg bg-indigo-600 px-5 py-2 text-sm font-semibold text-white transition hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {loading ? "Thinking…" : "Ask"}
        </button>
      </form>

      {result && (
        <div className="space-y-5">
          <div className="rounded-xl border border-indigo-800 bg-indigo-950/30 p-5">
            <h2 className="mb-2 text-xs font-semibold uppercase tracking-wider text-indigo-400">
              Answer
            </h2>
            <p className="text-sm leading-relaxed text-gray-200">
              {result.answer}
            </p>
          </div>

          {result.sources.length > 0 && (
            <div>
              <h2 className="mb-2 text-xs font-semibold uppercase tracking-wider text-gray-500">
                Sources
              </h2>
              <div className="space-y-2">
                {result.sources.map((src, i) => (
                  <div
                    key={i}
                    className="rounded-lg border border-gray-800 bg-gray-800/30 px-4 py-3"
                  >
                    <span className="mb-1 block text-xs font-medium text-indigo-400">
                      {src.month_key}
                    </span>
                    <p className="font-mono text-xs text-gray-500 leading-relaxed line-clamp-3">
                      {src.chunk_preview}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
