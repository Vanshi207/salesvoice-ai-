"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { api, json } from "@/lib/api";
import { STAGES, type Lead, type Page } from "@/lib/types";
import { Badge, Button, Card, ErrorText, inputClass } from "@/components/ui";

const PAGE_SIZE = 20;

export default function LeadsPage() {
  const [data, setData] = useState<Page<Lead> | null>(null);
  const [q, setQ] = useState("");
  const [stage, setStage] = useState("");
  const [offset, setOffset] = useState(0);
  const [showForm, setShowForm] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(() => {
    const params = new URLSearchParams({ limit: String(PAGE_SIZE), offset: String(offset) });
    if (q) params.set("q", q);
    if (stage) params.set("stage", stage);
    api<Page<Lead>>(`leads/leads?${params}`).then(setData).catch((e) => setError(e.message));
  }, [q, stage, offset]);

  useEffect(() => {
    const t = setTimeout(load, 300);
    return () => clearTimeout(t);
  }, [load]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Leads</h1>
        <Button onClick={() => setShowForm(!showForm)}>{showForm ? "Close" : "New lead"}</Button>
      </div>

      {showForm && <NewLeadForm onCreated={() => { setShowForm(false); load(); }} />}

      <div className="flex gap-3">
        <input placeholder="Search name, phone, company" value={q}
          onChange={(e) => { setQ(e.target.value); setOffset(0); }} className={inputClass} />
        <select value={stage} onChange={(e) => { setStage(e.target.value); setOffset(0); }}
          className="rounded-md border border-slate-300 px-3 py-2 text-sm">
          <option value="">All stages</option>
          {STAGES.map((s) => <option key={s} value={s}>{s.replace("_", " ")}</option>)}
        </select>
      </div>

      <ErrorText error={error} />
      <Card>
        {!data ? <p className="text-sm text-slate-500">Loading...</p> : (
          <>
            <table className="w-full text-left text-sm">
              <thead className="text-slate-500">
                <tr><th className="py-2">Name</th><th>Company</th><th>Phone</th><th>Stage</th><th>Score</th><th>Consent</th></tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {data.items.map((l) => (
                  <tr key={l.id} className="hover:bg-slate-50">
                    <td className="py-2">
                      <Link href={`/leads/${l.id}`} className="font-medium text-indigo-600 hover:underline">{l.name}</Link>
                    </td>
                    <td>{l.company ?? "-"}</td>
                    <td>{l.phone}</td>
                    <td><Badge value={l.stage} /></td>
                    <td>{l.score ?? "-"}</td>
                    <td>{l.dnd ? "DND" : l.consent ? "Yes" : "No"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {data.items.length === 0 && <p className="py-4 text-sm text-slate-500">No leads found.</p>}
            <div className="mt-4 flex items-center justify-between text-sm text-slate-500">
              <span>{data.total} leads</span>
              <div className="flex gap-2">
                <Button variant="secondary" disabled={offset === 0}
                  onClick={() => setOffset(offset - PAGE_SIZE)}>Previous</Button>
                <Button variant="secondary" disabled={offset + PAGE_SIZE >= data.total}
                  onClick={() => setOffset(offset + PAGE_SIZE)}>Next</Button>
              </div>
            </div>
          </>
        )}
      </Card>
    </div>
  );
}

function NewLeadForm({ onCreated }: { onCreated: () => void }) {
  const [form, setForm] = useState({ name: "", phone: "", company: "", email: "", language: "hi-en", consent: false });
  const [error, setError] = useState("");
  const set = (k: string, v: string | boolean) => setForm({ ...form, [k]: v });

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    try {
      await api("leads/leads", json({ ...form, company: form.company || null, email: form.email || null }));
      onCreated();
    } catch (err) {
      setError((err as Error).message);
    }
  }

  return (
    <Card title="New lead">
      <form onSubmit={submit} className="grid grid-cols-2 gap-3">
        <input required placeholder="Name" value={form.name} onChange={(e) => set("name", e.target.value)} className={inputClass} />
        <input required placeholder="Phone, e.g. +9198xxxxxxxx" value={form.phone} onChange={(e) => set("phone", e.target.value)} className={inputClass} />
        <input placeholder="Company" value={form.company} onChange={(e) => set("company", e.target.value)} className={inputClass} />
        <input type="email" placeholder="Email" value={form.email} onChange={(e) => set("email", e.target.value)} className={inputClass} />
        <select value={form.language} onChange={(e) => set("language", e.target.value)} className={inputClass}>
          <option value="hi-en">Hinglish</option><option value="hi">Hindi</option><option value="en">English</option>
        </select>
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" checked={form.consent} onChange={(e) => set("consent", e.target.checked)} />
          Lead agreed to be called
        </label>
        <div className="col-span-2 flex items-center gap-3">
          <Button type="submit">Save lead</Button>
          <ErrorText error={error} />
        </div>
      </form>
    </Card>
  );
}
