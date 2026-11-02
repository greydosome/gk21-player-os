"use client";

import { useEffect, useState } from "react";

export default function SessionControls() {
  const [enabled, setEnabled] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => {
    let stopped = false;
    async function check() {
      if (document.visibilityState !== "visible") return;
      try {
        const response = await fetch("/api/auth/check", { cache: "no-store" });
        if (stopped) return;
        if (response.status === 401) { window.location.replace("/login"); return; }
        if (response.ok) setEnabled(response.headers.get("X-GK21-Auth") === "enabled");
      } catch { /* Offline: leave the current screen intact. */ }
    }
    void check();
    const timer = setInterval(() => { void check(); }, 300000);
    window.addEventListener("focus", check);
    return () => { stopped = true; clearInterval(timer); window.removeEventListener("focus", check); };
  }, []);
  if (!enabled) return null;
  return <div className="flex justify-end gap-2 p-3 text-xs text-zinc-400">
    <span role="status">{error}</span>
    <button type="button" onClick={async () => {
      try {
        const response = await fetch("/api/auth/logout", { method: "POST", headers: {"Content-Type": "application/json"}, body: "{}" });
        if (!response.ok && response.status !== 401) throw new Error("logout failed");
        window.location.replace("/login");
      } catch { setError("연결을 확인한 뒤 다시 시도해 주세요."); }
    }}>로그아웃</button>
  </div>;
}
