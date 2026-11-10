import { NextRequest, NextResponse } from "next/server";
export async function GET(request: NextRequest) {
  const day = request.nextUrl.searchParams.get("record_date") ?? "";
  if (!/^\d{4}-\d{2}-\d{2}$/.test(day)) return NextResponse.json({error:"Invalid date"},{status:400});
  try {
    const res = await fetch(`http://127.0.0.1:8000/api/consumed-meals?record_date=${day}`, {cache:"no-store"});
    return NextResponse.json(await res.json(), {status:res.status,headers:{"Cache-Control":"no-store"}});
  } catch { return NextResponse.json({error:"Unavailable"},{status:502}); }
}
