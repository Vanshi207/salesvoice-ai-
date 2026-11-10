import Link from "next/link";
import type { Call } from "@/lib/types";
import { Badge, fmtDate, fmtDuration } from "./ui";

export function CallsTable({ calls }: { calls: Call[] }) {
  if (calls.length === 0) return <p className="text-sm text-slate-500">No calls yet.</p>;
  return (
    <table className="w-full text-left text-sm">
      <thead className="text-slate-500">
        <tr><th className="py-2">When</th><th>Source</th><th>Duration</th><th>Status</th><th></th></tr>
      </thead>
      <tbody className="divide-y divide-slate-100">
        {calls.map((c) => (
          <tr key={c.id}>
            <td className="py-2">{fmtDate(c.created_at)}</td>
            <td>{c.source === "agent" ? "AI agent" : "Upload"}</td>
            <td>{fmtDuration(c.duration_s)}</td>
            <td><Badge value={c.status} /></td>
            <td className="text-right">
              <Link href={`/calls/${c.id}`} className="text-indigo-600 hover:underline">Open</Link>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
