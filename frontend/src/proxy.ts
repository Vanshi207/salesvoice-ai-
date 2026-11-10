import { NextRequest, NextResponse } from "next/server";

export function proxy(req: NextRequest) {
  if (!req.cookies.has("sv_refresh")) {
    return NextResponse.redirect(new URL("/login", req.url));
  }
  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!login|api|_next|favicon.ico).*)"],
};
