import { NextRequest, NextResponse } from "next/server";
import { GATEWAY_URL, clearTokens, setTokens } from "@/lib/session";

export async function POST(req: NextRequest) {
  const body = await req.json();
  let r: Response;
  try {
    r = await fetch(`${GATEWAY_URL}/api/auth/login`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ email: body.email, password: body.password }),
    });
  } catch {
    return NextResponse.json({ detail: "Backend is not reachable. Is Docker running?" }, { status: 502 });
  }
  if (!r.ok) {
    let detail: string;
    try {
      const data = await r.json();
      detail = typeof data.detail === "string" ? data.detail : `Login failed (${r.status})`;
    } catch {
      detail = r.status === 429 ? "Too many attempts, wait a minute" :
               r.status === 401 ? "Wrong email or password" : `Login failed (${r.status})`;
    }
    return NextResponse.json({ detail }, { status: r.status });
  }
  const res = NextResponse.json({ ok: true });
  setTokens(res, await r.json());
  return res;
}

export async function DELETE() {
  const res = NextResponse.json({ ok: true });
  clearTokens(res);
  return res;
}
