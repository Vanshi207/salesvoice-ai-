"use client";

import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { api, json } from "@/lib/api";
import { STAGES, isFinished, type Call, type FollowUp, type Lead, type Page, type User } from "@/lib/types";
import { usePolling } from "@/lib/usePolling";
import { Badge, Button, Card, ErrorText, fmtDate, inputClass } from "@/components/ui";
import { CallsTable } from "@/components/CallsTable";
import { UploadCall } from "@/components/UploadCall";
import { WebRTCCall } from "@/components/WebRTCCall";

export default function LeadDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [lead, setLead] = useState<Lead | null>(null);
  const [me, setMe] = useState<User | null>(null);
  const [calls, setCalls] = useState<Call[]>([]);
  const [followups, setFollowups] = useState<FollowUp[]>([]);
  const [error, setError] = useState("");

  const load = useCallback(() => {
    Promise.all([
      api<Lead>(`leads/leads/${id}`),
      api<Page<Call>>(`calls/calls?lead_id=${id}&limit=50`),
      api<FollowUp[]>(`leads/leads/${id}/followups`),
      api<User>("auth/me"),
    ]).then(([l, c, f, u]) => { setLead(l); setCalls(c.items); setFollowups(f); setMe(u); })
      .catch((e) => setError(e.message));
  }, [id]);

  useEffect(load, [load]);
  usePolling(load, calls.some((c) => !isFinished(c.status)));

  async function update(changes: Partial<Lead>) {
    try {
      setLead(await api<Lead>(`leads/leads/${id}`, json(changes, "PATCH")));
    } catch (e) {
      setError((e as Error).message);
    }
  }

  async function remove() {
    if (!confirm(`Delete ${lead?.name}?`)) return;
    await api(`leads/leads/${id}`, { method: "DELETE" });
    router.push("/leads");
  }

  if (error) return <ErrorText error={error} />;
  if (!lead) return <p className="text-slate-500">Loading...</p>;

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-semibold">{lead.name}</h1>
          <p className="text-sm text-slate-500">
            {lead.phone} · {lead.company ?? "No company"} · {lead.email ?? "No email"} · language {lead.language}
          </p>
        </div>
        <div className="text-right">
          <p className="text-sm text-slate-500">Lead score</p>
          <p className="text-3xl font-semibold">{lead.score ?? "-"}</p>
        </div>
      </div>

      <Card title="Talk to this lead (AI voice agent)">
        {me ? (
          <WebRTCCall leadId={lead.id} leadName={lead.name} userId={me.id} userRole={me.role} />
        ) : (
          <p className="text-sm text-slate-500">Loading...</p>
        )}
        <p className="mt-3 text-xs text-slate-400">
          Uses your microphone to talk with the AI sales agent. The agent searches the knowledge base during the call.
          After the call ends, the recording is uploaded and analysed automatically.
        </p>
      </Card>

      <Card title="Status">
        <div className="flex flex-wrap items-center gap-6 text-sm">
          <label className="flex items-center gap-2">Stage
            <select value={lead.stage} onChange={(e) => update({ stage: e.target.value as Lead["stage"] })}
              className="rounded-md border border-slate-300 px-2 py-1">
              {STAGES.map((s) => <option key={s} value={s}>{s.replace("_", " ")}</option>)}
            </select>
            <Badge value={lead.stage} />
          </label>
          <label className="flex items-center gap-2">
            <input type="checkbox" checked={lead.consent} onChange={(e) => update({ consent: e.target.checked })} />
            Consent to be called
          </label>
          <label className="flex items-center gap-2">
            <input type="checkbox" checked={lead.dnd} onChange={(e) => update({ dnd: e.target.checked })} />
            Do-Not-Disturb
          </label>
          <Button variant="danger" onClick={remove} className="ml-auto">Delete lead</Button>
        </div>
      </Card>

      <Card title="Calls">
        <div className="space-y-4">
          <UploadCall leadId={lead.id} onUploaded={load} />
          <CallsTable calls={calls} />
        </div>
      </Card>

      <FollowUps leadId={lead.id} items={followups} onAdded={load} />
    </div>
  );
}

function FollowUps({ leadId, items, onAdded }: { leadId: string; items: FollowUp[]; onAdded: () => void }) {
  const [when, setWhen] = useState("");
  const [note, setNote] = useState("");
  const [error, setError] = useState("");

  async function add(e: React.FormEvent) {
    e.preventDefault();
    try {
      await api(`leads/leads/${leadId}/followups`,
        json({ scheduled_at: new Date(when).toISOString(), note: note || null }));
      setWhen(""); setNote(""); setError("");
      onAdded();
    } catch (err) {
      setError((err as Error).message);
    }
  }

  return (
    <Card title="Follow-ups">
      <ul className="mb-4 divide-y divide-slate-100 text-sm">
        {items.map((f) => (
          <li key={f.id} className="flex justify-between py-2">
            <span>{fmtDate(f.scheduled_at)} · {f.note ?? "No note"}</span>
            <Badge value={f.status} />
          </li>
        ))}
        {items.length === 0 && <li className="py-2 text-slate-500">No follow-ups yet.</li>}
      </ul>
      <form onSubmit={add} className="flex gap-2">
        <input type="datetime-local" required value={when} onChange={(e) => setWhen(e.target.value)} className={inputClass} />
        <input placeholder="Note" value={note} onChange={(e) => setNote(e.target.value)} className={inputClass} />
        <Button type="submit">Add</Button>
      </form>
      <ErrorText error={error} />
    </Card>
  );
}
