"use client";

import { useCallback, useEffect, useState } from "react";
import { api, json } from "@/lib/api";
import type { Doc, SearchHit } from "@/lib/types";
import { Badge, Button, Card, ErrorText, fmtDate, inputClass } from "@/components/ui";

export default function KnowledgePage() {
  const [docs, setDocs] = useState<Doc[] | null>(null);
  const [error, setError] = useState("");

  const load = useCallback(() => {
    api<Doc[]>("knowledge/documents").then(setDocs).catch((e) => setError(e.message));
  }, []);
  useEffect(load, [load]);

  async function remove(d: Doc) {
    if (!confirm(`Delete ${d.title}?`)) return;
    try {
      await api(`knowledge/documents/${d.id}`, { method: "DELETE" });
      load();
    } catch (e) {
      setError((e as Error).message);
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Knowledge base</h1>
      <p className="text-sm text-slate-500">
        The AI agent searches these documents during calls (product details, pricing, FAQs).
      </p>
      <UploadDoc onUploaded={load} />
      <ErrorText error={error} />
      <Card title="Documents">
        {!docs ? <p className="text-sm text-slate-500">Loading...</p> : (
          <ul className="divide-y divide-slate-100 text-sm">
            {docs.map((d) => (
              <li key={d.id} className="flex items-center gap-3 py-2">
                <span className="flex-1 font-medium">{d.title}</span>
                <span className="text-slate-500">{d.chunk_count} chunks · {fmtDate(d.created_at)}</span>
                <Badge value={d.status} />
                <Button variant="secondary" onClick={() => remove(d)}>Delete</Button>
              </li>
            ))}
            {docs.length === 0 && <li className="py-2 text-slate-500">No documents yet.</li>}
          </ul>
        )}
      </Card>
      <SearchTester />
    </div>
  );
}

function UploadDoc({ onUploaded }: { onUploaded: () => void }) {
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState("");
  const [busy, setBusy] = useState(false);
  const [inputKey, setInputKey] = useState(0);
  const [error, setError] = useState("");

  async function upload() {
    if (!file) return;
    const form = new FormData();
    form.append("file", file);
    if (title) form.append("title", title);
    setBusy(true);
    setError("");
    try {
      await api("knowledge/documents", { method: "POST", body: form });
      setFile(null); setInputKey(inputKey + 1); setTitle("");
      onUploaded();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card title="Upload a document (admins)">
      <div className="flex items-center gap-2">
        <input key={inputKey} type="file" accept=".pdf,.txt,.md" onChange={(e) => setFile(e.target.files?.[0] ?? null)} className="text-sm" />
        <input placeholder="Title (optional)" value={title} onChange={(e) => setTitle(e.target.value)} className={inputClass} />
        <Button onClick={upload} disabled={!file || busy}>{busy ? "Uploading..." : "Upload"}</Button>
      </div>
      <ErrorText error={error} />
    </Card>
  );
}

function SearchTester() {
  const [query, setQuery] = useState("");
  const [hits, setHits] = useState<SearchHit[] | null>(null);
  const [error, setError] = useState("");

  async function search(e: React.FormEvent) {
    e.preventDefault();
    try {
      setHits((await api<{ hits: SearchHit[] }>("knowledge/search", json({ query, top_k: 3 }))).hits);
      setError("");
    } catch (err) {
      setError((err as Error).message);
    }
  }

  return (
    <Card title="Test a question">
      <form onSubmit={search} className="flex gap-2">
        <input required placeholder="e.g. What does the premium plan cost?" value={query}
          onChange={(e) => setQuery(e.target.value)} className={inputClass} />
        <Button type="submit">Search</Button>
      </form>
      <ErrorText error={error} />
      {hits && (
        <ul className="mt-4 space-y-3 text-sm">
          {hits.map((h) => (
            <li key={h.chunk_id} className="rounded-md bg-slate-50 p-3">
              <p className="text-xs text-slate-500">{h.document_title} · match {h.score.toFixed(2)}</p>
              <p>{h.text}</p>
            </li>
          ))}
          {hits.length === 0 && <li className="text-slate-500">Nothing relevant found.</li>}
        </ul>
      )}
    </Card>
  );
}
