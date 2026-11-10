import { NextRequest, NextResponse } from "next/server";
import { ACCESS_COOKIE, GATEWAY_URL, REFRESH_COOKIE, Tokens, refreshTokens, setTokens } from "@/lib/session";

async function forward(req: NextRequest, ctx: RouteContext<"/api/gw/[...path]">) {
  const { path } = await ctx.params;
  const url = `${GATEWAY_URL}/api/${path.join("/")}${req.nextUrl.search}`;
  const body = ["GET", "HEAD"].includes(req.method) ? undefined : await req.arrayBuffer();

  const send = (token?: string) => {
    const headers = new Headers();
    const ct = req.headers.get("content-type");
    if (ct) headers.set("content-type", ct);
    if (token) headers.set("authorization", `Bearer ${token}`);
    return fetch(url, { method: req.method, headers, body, redirect: "manual" });
  };

  let newTokens: Tokens | null = null;
  let upstream: Response;
  try {
    upstream = await send(req.cookies.get(ACCESS_COOKIE)?.value);

    const refresh = req.cookies.get(REFRESH_COOKIE)?.value;
    if (upstream.status === 401 && refresh) {
      newTokens = await refreshTokens(refresh);
      if (newTokens) upstream = await send(newTokens.access_token);
    }
  } catch {
    return NextResponse.json({ detail: "Backend is not reachable. Is Docker running?" }, { status: 502 });
  }

  const headers = new Headers();
  for (const h of ["content-type", "cache-control", "location"]) {
    const v = upstream.headers.get(h);
    if (v) headers.set(h, v);
  }
  const res = new NextResponse(upstream.body, { status: upstream.status, headers });
  if (newTokens) setTokens(res, newTokens);
  return res;
}

export { forward as GET, forward as POST, forward as PATCH, forward as PUT, forward as DELETE };
