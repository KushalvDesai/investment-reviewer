"use client";

import { useCallback, useRef, useState } from "react";

import { uploadPdf, type UploadResponse } from "@/lib/api";

interface UploadZoneProps {
  onSuccess?: (result: UploadResponse) => void;
}

export default function UploadZone({ onSuccess }: UploadZoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [status, setStatus] = useState<"idle" | "uploading" | "success" | "error">("idle");
  const [message, setMessage] = useState("");
  const [result, setResult] = useState<UploadResponse | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback(
    async (file: File) => {
      if (!file.name.toLowerCase().endsWith(".pdf")) {
        setStatus("error");
        setMessage("Only PDF files are supported.");
        return;
      }
      setStatus("uploading");
      setMessage(`Uploading ${file.name}…`);
      setResult(null);
      try {
        const res = await uploadPdf(file);
        setStatus("success");
        setMessage(
          `Indexed ${res.chunks_indexed} chunks for month ${res.month_key}.`
        );
        setResult(res);
        onSuccess?.(res);
      } catch (err: unknown) {
        setStatus("error");
        setMessage(err instanceof Error ? err.message : "Upload failed.");
      }
    },
    [onSuccess]
  );

  const onDrop = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      setIsDragging(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  const onInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  const borderColor =
    isDragging
      ? "border-indigo-500 bg-indigo-950/30"
      : status === "success"
      ? "border-emerald-600 bg-emerald-950/20"
      : status === "error"
      ? "border-rose-600 bg-rose-950/20"
      : "border-gray-700 bg-gray-800/40 hover:border-gray-500";

  return (
    <div
      className={`cursor-pointer rounded-xl border-2 border-dashed p-10 text-center transition-all ${borderColor}`}
      onDragOver={(e) => {
        e.preventDefault();
        setIsDragging(true);
      }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={onDrop}
      onClick={() => inputRef.current?.click()}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".pdf"
        className="hidden"
        onChange={onInputChange}
      />

      {status === "uploading" ? (
        <div className="flex flex-col items-center gap-3">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-indigo-500 border-t-transparent" />
          <p className="text-sm text-gray-400">{message}</p>
        </div>
      ) : status === "success" && result ? (
        <div className="flex flex-col items-center gap-2">
          <span className="text-3xl text-emerald-400">✓</span>
          <p className="text-sm font-medium text-emerald-400">{message}</p>
          <p className="text-xs text-gray-500">
            Namespace: <span className="font-mono">{result.namespace}</span>
          </p>
          <p className="mt-2 text-xs text-gray-600">
            Click or drag another PDF to upload more.
          </p>
        </div>
      ) : status === "error" ? (
        <div className="flex flex-col items-center gap-2">
          <span className="text-3xl text-rose-400">✗</span>
          <p className="text-sm text-rose-400">{message}</p>
          <p className="mt-2 text-xs text-gray-500">
            Click or drag a PDF to try again.
          </p>
        </div>
      ) : (
        <div className="flex flex-col items-center gap-3">
          <svg
            className="h-10 w-10 text-gray-600"
            fill="none"
            stroke="currentColor"
            strokeWidth={1.5}
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5"
            />
          </svg>
          <p className="text-sm text-gray-400">
            Drag &amp; drop a PDF here, or{" "}
            <span className="text-indigo-400 underline">browse</span>
          </p>
          <p className="text-xs text-gray-600">Bank or investment statements only</p>
        </div>
      )}
    </div>
  );
}
