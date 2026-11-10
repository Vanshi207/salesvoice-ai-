"use client";

import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import { isFinished, type Call, type Page } from "@/lib/types";
import { usePolling } from "@/lib/usePolling";
import { Card, ErrorText } from "@/components/ui";
import { CallsTable } from "@/components/CallsTable";

export default function CallsPage() {
  const [calls, setCalls] = useState<Call[] | null>(null);
  const [error, setError] = useState("");

  const load = useCallback(() => {
    api<Page<Call>>("calls/calls?limit=50").then((p) => setCalls(p.items)).catch((e) => setError(e.message));
  }, []);

  useEffect(load, [load]);
  usePolling(load, !!calls?.some((c) => !isFinished(c.status)));

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Calls</h1>
      <p className="text-sm text-slate-500">
        To upload a recording, open a lead and use &quot;Upload recording&quot;. Agent calls appear here automatically.
      </p>
      <ErrorText error={error} />
      <Card>{calls ? <CallsTable calls={calls} /> : <p className="text-sm text-slate-500">Loading...</p>}</Card>
    </div>
  );
}
