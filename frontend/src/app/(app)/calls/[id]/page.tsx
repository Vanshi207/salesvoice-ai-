"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { api, json } from "@/lib/api";
import { isFinished, type CallDetail } from "@/lib/types";
import { usePolling } from "@/lib/usePolling";
import { Badge, Button, Card, ErrorText, fmtDate, fmtDuration } from "@/components/ui";

const STEPS = ["queued", "transcribing", "analyzing", "done"];

export default function CallDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [call, setCall] = useState<CallDetail | null>(null);
  const [error, setError] = useState("");

  const load = useCallback(() => {
    api<CallDetail>(`calls/calls/${id}`).then(setCall).catch((e) => setError(e.message));
  }, [id]);

  useEffect(load, [load]);
  usePolling(load, !!call && !isFinished(call.status));

  async function retry() {
    await api(`calls/calls/${id}/retry`, { method: "POST" });
    load();
  }

  async function swapSpeakers() {
    if (!call) return;
    setCall(await api<CallDetail>(`calls/calls/${id}`, json({ rep_speaker: call.rep_speaker === 0 ? 1 : 0 }, "PATCH")));
  }

  if (error) return <ErrorText error={error} />;
  if (!call) return <p className="text-slate-500">Loading...</p>;
  const a = call.analysis;

  return (
    <div className="space-y-6">
      <div>
        <Link href={`/leads/${call.lead_id}`} className="text-sm text-indigo-600 hover:underline">Back to lead</Link>
        <h1 className="text-2xl font-semibold">Call on {fmtDate(call.created_at)}</h1>
        <p className="text-sm text-slate-500">
          {call.source === "agent" ? "AI agent call" : `Uploaded: ${call.filename}`} · {fmtDuration(call.duration_s)}
          {call.languages && ` · languages: ${call.languages}`}
        </p>
      </div>

      <Card title="Processing">
        <div className="flex items-center gap-2 text-sm">
          {STEPS.map((s, i) => (
            <span key={s} className={i <= STEPS.indexOf(call.status) ? "font-medium text-indigo-700" : "text-slate-400"}>
              {s}{i < STEPS.length - 1 && " →"}
            </span>
          ))}
          <span className="ml-auto"><Badge value={call.status} /></span>
        </div>
        {call.status === "failed" && (
          <div className="mt-3 flex items-center gap-3">
            <ErrorText error={call.error ?? "Failed"} />
            <Button variant="secondary" onClick={retry}>Retry</Button>
          </div>
        )}
      </Card>

      {a && (
        <>
          <div className="grid grid-cols-3 gap-4">
            <Card title="Lead score"><p className="text-4xl font-semibold">{a.lead_score}</p></Card>
            <Card title="Sentiment"><Badge value={a.sentiment} /></Card>
            <Card title="Buying intent"><p className="text-lg font-medium capitalize">{a.intent}</p></Card>
          </div>

          <Card title="Summary">
            <p className="text-sm leading-6">{a.summary}</p>
            <h3 className="mt-4 text-sm font-medium">Why this score</h3>
            <ul className="ml-5 list-disc text-sm">{a.result.score_reasons.map((r) => <li key={r}>{r}</li>)}</ul>
            <h3 className="mt-4 text-sm font-medium">Next steps</h3>
            <ul className="ml-5 list-disc text-sm">{a.result.next_steps.map((r) => <li key={r}>{r}</li>)}</ul>
          </Card>

          <Card title="Objections">
            {a.result.objections.length === 0 ? <p className="text-sm text-slate-500">No objections raised.</p> : (
              <ul className="space-y-2 text-sm">
                {a.result.objections.map((o, i) => (
                  <li key={i} className="flex items-start gap-3">
                    <Badge value={o.category} />
                    <span className="flex-1 italic">&ldquo;{o.quote}&rdquo;</span>
                    <span className={o.handled ? "text-green-700" : "text-red-600"}>
                      {o.handled ? "handled" : "not handled"}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </Card>

          <Card title="Talk metrics">
            <div className="grid grid-cols-4 gap-4 text-sm">
              <Metric label="Rep talk ratio" value={`${Math.round((a.metrics.rep_talk_ratio ?? 0) * 100)}%`} />
              <Metric label="Longest rep monologue" value={`${a.metrics.longest_rep_monologue_s ?? 0}s`} />
              <Metric label="Rep questions" value={a.metrics.rep_questions ?? 0} />
              <Metric label="Customer questions" value={a.metrics.customer_questions ?? 0} />
            </div>
          </Card>
        </>
      )}

      {call.segments.length > 0 && (
        <Card title="Transcript" action={<Button variant="secondary" onClick={swapSpeakers}>Swap rep / customer</Button>}>
          <div className="space-y-2 text-sm">
            {call.segments.map((s, i) => {
              const isRep = s.speaker === call.rep_speaker;
              return (
                <div key={i} className={`flex ${isRep ? "justify-start" : "justify-end"}`}>
                  <div className={`max-w-[75%] rounded-lg px-3 py-2 ${isRep ? "bg-indigo-50" : "bg-slate-100"}`}>
                    <p className="text-xs text-slate-500">{isRep ? "Rep" : "Customer"} · {fmtDuration(s.start_s)}</p>
                    <p>{s.text}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </Card>
      )}
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string | number }) {
  return (
    <div>
      <p className="text-slate-500">{label}</p>
      <p className="text-xl font-semibold">{value}</p>
    </div>
  );
}
