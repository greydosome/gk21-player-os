import { NextRequest, NextResponse } from "next/server";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();

    const res = await fetch("http://127.0.0.1:8000/api/day", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });

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
