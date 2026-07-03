import { NextRequest, NextResponse } from "next/server";

export async function GET(request: NextRequest) {
  try {
    const recordDate = request.nextUrl.searchParams.get("record_date");

    const url = recordDate
      ? `http://127.0.0.1:8000/api/dashboard?record_date=${recordDate}`
      : "http://127.0.0.1:8000/api/dashboard";

    const res = await fetch(url, { cache: "no-store" });
    const text = await res.text();

    let data;
    try {
      data = JSON.parse(text);
    } catch {
      data = {
        success: false,
        raw: text,
      };
    }

    return NextResponse.json(data, {
      status: res.status,
    });
  } catch (error) {
    return NextResponse.json(
      {
        success: false,
        error: String(error),
      },
      { status: 500 }
    );
  }
}
