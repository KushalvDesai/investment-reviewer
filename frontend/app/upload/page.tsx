"use client";

import { useState } from "react";

import UploadZone from "@/components/UploadZone";
import { deleteMonth, listMonths, type UploadResponse } from "@/lib/api";
import { useEffect } from "react";

export default function UploadPage() {
  const [months, setMonths] = useState<string[]>([]);
  const [deletingMonth, setDeletingMonth] = useState<string | null>(null);
  const [deleteError, setDeleteError] = useState("");

  function refreshMonths() {
    listMonths().then(setMonths).catch(console.error);
  }

  useEffect(() => {
    refreshMonths();
  }, []);

  function handleUploadSuccess(result: UploadResponse) {
    refreshMonths();
  }

  async function handleDelete(monthKey: string) {
    setDeletingMonth(monthKey);
    setDeleteError("");
    try {
      await deleteMonth(monthKey);
      refreshMonths();
    } catch (err: unknown) {
      setDeleteError(err instanceof Error ? err.message : "Delete failed.");
    } finally {
      setDeletingMonth(null);
    }
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-white">Upload Statements</h1>
        <p className="mt-1 text-sm text-gray-500">
          Upload PDF bank or investment statements. Each statement is
          automatically indexed by its month.
        </p>
      </div>

      <UploadZone onSuccess={handleUploadSuccess} />

      <div>
        <h2 className="mb-3 text-sm font-semibold text-gray-400 uppercase tracking-wider">
          Indexed Months
        </h2>
        {deleteError && (
          <p className="mb-3 rounded-lg border border-rose-700 bg-rose-950/30 px-4 py-2 text-sm text-rose-400">
            {deleteError}
          </p>
        )}
        {months.length === 0 ? (
          <p className="text-sm text-gray-600">No statements indexed yet.</p>
        ) : (
          <ul className="divide-y divide-gray-800 rounded-xl border border-gray-700 overflow-hidden">
            {months.map((m) => (
              <li
                key={m}
                className="flex items-center justify-between px-4 py-3 bg-gray-800/30 hover:bg-gray-800/50 transition-colors"
              >
                <span className="font-mono text-sm text-gray-200">{m}</span>
                <button
                  onClick={() => handleDelete(m)}
                  disabled={deletingMonth === m}
                  className="rounded-md px-3 py-1 text-xs font-medium text-rose-400 hover:bg-rose-900/30 transition-colors disabled:opacity-50"
                >
                  {deletingMonth === m ? "Deleting…" : "Delete"}
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
