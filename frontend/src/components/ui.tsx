import type { ReactNode } from "react";

const COLORS: Record<string, string> = {
  // lead stages
  new: "bg-slate-100 text-slate-700", contacted: "bg-blue-100 text-blue-700",
  hot: "bg-orange-100 text-orange-700", follow_up: "bg-purple-100 text-purple-700",
  won: "bg-green-100 text-green-700", lost: "bg-red-100 text-red-700",
  // call / document status
  queued: "bg-slate-100 text-slate-700", transcribing: "bg-blue-100 text-blue-700",
  analyzing: "bg-amber-100 text-amber-700", processing: "bg-amber-100 text-amber-700",
  done: "bg-green-100 text-green-700", ready: "bg-green-100 text-green-700",
  failed: "bg-red-100 text-red-700",
  // sentiment
  positive: "bg-green-100 text-green-700", neutral: "bg-slate-100 text-slate-700",
  negative: "bg-red-100 text-red-700", mixed: "bg-amber-100 text-amber-700",
};

export function Badge({ value }: { value: string }) {
  return (
    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${COLORS[value] ?? "bg-slate-100 text-slate-700"}`}>
      {value.replace("_", " ")}
    </span>
  );
}

export function Card({ title, children, action }: { title?: string; children: ReactNode; action?: ReactNode }) {
  return (
    <section className="rounded-xl bg-white p-6 shadow-sm">
      {(title || action) && (
        <div className="mb-4 flex items-center justify-between">
          {title && <h2 className="font-medium">{title}</h2>}
          {action}
        </div>
      )}
      {children}
    </section>
  );
}

export function Button({ children, variant = "primary", ...props }:
  React.ButtonHTMLAttributes<HTMLButtonElement> & { variant?: "primary" | "secondary" | "danger" }) {
  const styles = {
    primary: "bg-indigo-600 text-white hover:bg-indigo-700",
    secondary: "border border-slate-300 bg-white text-slate-700 hover:bg-slate-50",
    danger: "bg-red-600 text-white hover:bg-red-700",
  };
  return (
    <button {...props}
      className={`rounded-md px-3 py-2 text-sm font-medium disabled:opacity-50 ${styles[variant]} ${props.className ?? ""}`}>
      {children}
    </button>
  );
}

export const inputClass = "w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900";

export function ErrorText({ error }: { error: string }) {
  return error ? <p className="text-sm text-red-600">{error}</p> : null;
}

export const fmtDate = (iso: string) =>
  new Date(iso).toLocaleString("en-IN", { dateStyle: "medium", timeStyle: "short" });

export const fmtDuration = (s: number | null) =>
  s == null ? "-" : `${Math.floor(s / 60)}:${String(Math.round(s % 60)).padStart(2, "0")}`;
