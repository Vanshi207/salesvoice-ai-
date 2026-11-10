"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import type { Call } from "@/lib/types";
import { Button, ErrorText } from "./ui";

export function UploadCall({ leadId, onUploaded }: { leadId: string; onUploaded: (c: Call) => void }) {
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [inputKey, setInputKey] = useState(0);
  const [error, setError] = useState("");

  async function upload() {
    if (!file) return;
    const form = new FormData();
    form.append("file", file);
    form.append("lead_id", leadId);
    setBusy(true);
    setError("");
    try {
      onUploaded(await api<Call>("calls/calls", { method: "POST", body: form }));
      setFile(null); setInputKey(inputKey + 1);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <input key={inputKey} type="file" accept=".mp3,.wav,.m4a,.ogg"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)} className="text-sm" />
        <Button onClick={upload} disabled={!file || busy}>{busy ? "Uploading..." : "Upload recording"}</Button>
      </div>
      <ErrorText error={error} />
    </div>
  );
}
