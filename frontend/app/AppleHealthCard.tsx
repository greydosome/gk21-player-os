"use client";

import { useEffect, useState } from "react";

type Health = {
  enabled: boolean;
  status?: string;
  coaching_status?: string;
  collected_at?: string;
  metric_collected_at?: Record<string, string>;
  summary?: { sleep_hours?: number; weight_kg?: number; workouts?: { workout_type: string; minutes: number }[] };
};

export default function AppleHealthCard({ recordDate }: { recordDate: string }) {
  const [health, setHealth] = useState<Health | null>(null);
  const [failed, setFailed] = useState(false);
  useEffect(() => {
    let cancelled = false;
    const controller = new AbortController();
    async function refresh() {
      try {
        const res = await fetch(`/api/dashboard?record_date=${encodeURIComponent(recordDate)}`, { cache: "no-store", signal: controller.signal });
        if (!res.ok) throw new Error("load failed");
        const data = await res.json();
        if (!data.success) throw new Error("load failed");
        if (!cancelled) { setHealth(data.apple_health ? { ...data.apple_health, coaching_status: data.ai?.overview?.status } : null); setFailed(false); }
      } catch { if (!cancelled) setFailed(true); }
    }
    void refresh();
    const timer = setInterval(() => { if (document.visibilityState === "visible") void refresh(); }, 60000);
    return () => { cancelled = true; controller.abort(); clearInterval(timer); };
  }, [recordDate]);
  if (!health?.enabled) return null;
  const summary = health.summary;
  const time = (value: string) => new Date(value).toLocaleString("ko-KR", { timeZone: "Asia/Seoul" });
  return <section className="mt-5 rounded-2xl border border-zinc-700 bg-zinc-900 p-4" aria-label="Apple 건강 자동 기록">
    <h2 className="font-semibold text-zinc-100">Apple 건강 · 자동 기록</h2>
    <p className="mt-1 text-xs text-zinc-400" role="status">{failed ? "동기화 상태를 확인할 수 없습니다." : health.status === "missing" ? "아직 받은 기록이 없습니다. 아이폰에서 단축어를 실행해 주세요." : `${health.status === "stale" ? "최근 동기화가 지연되었습니다. " : ""}마지막 수집: ${time(health.collected_at!)}`}</p>
    {summary && health.coaching_status !== "COMPLETED" && <p className="mt-2 text-xs text-amber-300">최근 기록을 반영한 코칭은 아직 준비되지 않았습니다.</p>}
    {summary && <div className="mt-3 space-y-2 text-sm text-zinc-200">
      <p>수면: {summary.sleep_hours == null ? "미수집" : `${summary.sleep_hours}시간`}</p>
      <p>체중: {summary.weight_kg == null ? "미수집" : `${summary.weight_kg}kg`}</p>
      <p>운동: {summary.workouts == null ? "미수집" : summary.workouts.length === 0 ? "수집 구간에 기록 없음" : summary.workouts.map(w => `${w.workout_type} ${w.minutes}분`).join(" · ")}</p>
      {Object.entries(health.metric_collected_at ?? {}).filter(([key]) => key !== "weight_measured_at").map(([key, value]) => <p className="text-xs text-zinc-500" key={key}>{({sleep_hours: "수면", weight_kg: "체중", workouts: "운동"} as Record<string,string>)[key] ?? key} 수집: {time(value)}</p>)}
    </div>}
    <p className="mt-3 text-xs text-zinc-400">직접 작성한 기록과 별도로 보관하며 코칭에 참고합니다. 누락된 항목은 0으로 처리하지 않습니다.</p>
  </section>;
}
