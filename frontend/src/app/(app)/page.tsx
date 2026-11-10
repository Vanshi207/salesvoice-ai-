"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { STAGES, type Call, type Lead, type Page, type User } from "@/lib/types";
import { Badge, Card, ErrorText } from "@/components/ui";
import { CallsTable } from "@/components/CallsTable";

export default function OverviewPage() {
  const [me, setMe] = useState<User | null>(null);
  const [counts, setCounts] = useState<Record<string, number> | null>(null);
  const [hot, setHot] = useState<Lead[]>([]);
  const [calls, setCalls] = useState<Call[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    const stageCounts = Promise.all(STAGES.map((s) => api<Page<Lead>>(`leads/leads?stage=${s}&limit=1`)));
    Promise.all([api<User>("auth/me"), stageCounts, api<Page<Lead>>("leads/leads?stage=hot&limit=5"),
                 api<Page<Call>>("calls/calls?limit=5")])
      .then(([u, pages, h, c]) => {
        setMe(u);
        setCounts(Object.fromEntries(STAGES.map((s, i) => [s, pages[i].total])));
        setHot(h.items);
        setCalls(c.items);
      })
      .catch((e) => setError(e.message));
  }, []);

  if (error) return <ErrorText error={error} />;
  if (!me || !counts) return <p className="text-slate-500">Loading...</p>;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Welcome, {me.name}</h1>
        <p className="text-sm text-slate-500">Signed in as {me.email} ({me.role})</p>
      </div>

      <div className="grid grid-cols-3 gap-4 md:grid-cols-6">
        {STAGES.map((s) => (
          <Link key={s} href="/leads" className="rounded-xl bg-white p-4 shadow-sm hover:shadow">
            <Badge value={s} />
            <p className="mt-2 text-2xl font-semibold">{counts[s]}</p>
          </Link>
        ))}
      </div>

      <Card title="Hot leads">
        <ul className="divide-y divide-slate-100 text-sm">
          {hot.map((l) => (
            <li key={l.id} className="flex justify-between py-2">
              <Link href={`/leads/${l.id}`} className="text-indigo-600 hover:underline">{l.name}</Link>
              <span className="text-slate-500">score {l.score ?? "-"}</span>
            </li>
          ))}
          {hot.length === 0 && <li className="py-2 text-slate-500">No hot leads yet.</li>}
        </ul>
      </Card>

      <Card title="Recent calls"><CallsTable calls={calls} /></Card>
    </div>
  );
}
