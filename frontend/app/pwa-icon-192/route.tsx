import { ImageResponse } from "next/og";

export async function GET() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 110,
          background: "#0f172a",
        }}
      >
        🧤
      </div>
    ),
    { width: 192, height: 192 }
  );
}
