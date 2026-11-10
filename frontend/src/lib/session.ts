import "server-only";
import type { NextResponse } from "next/server";

export const ACCESS_COOKIE = "sv_access";
export const REFRESH_COOKIE = "sv_refresh";
export const GATEWAY_URL = process.env.GATEWAY_URL ?? "http://localhost:8000";

export type Tokens = { access_token: string; refresh_token: string };

const base = {
  httpOnly: true,
  secure: process.env.NODE_ENV === "production",
  sameSite: "lax" as const,
  path: "/",
};

export function setTokens(res: NextResponse, t: Tokens) {
  res.cookies.set(ACCESS_COOKIE, t.access_token, { ...base, maxAge: 15 * 60 });
  res.cookies.set(REFRESH_COOKIE, t.refresh_token, { ...base, maxAge: 7 * 24 * 60 * 60 });
}

export function clearTokens(res: NextResponse) {
  res.cookies.delete(ACCESS_COOKIE);
  res.cookies.delete(REFRESH_COOKIE);
}

export async function refreshTokens(refreshToken: string): Promise<Tokens | null> {
  const r = await fetch(`${GATEWAY_URL}/api/auth/refresh`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
  return r.ok ? r.json() : null;
}
