type Dashboard = {
  gk_readiness_score?: number | null;
  gk_readiness_level?: string | null;
  gk_readiness_message?: string | null;
};

export default function GKReadyCard({ dashboard }: { dashboard: Dashboard }) {
  const level = dashboard.gk_readiness_level ?? "NORMAL";
  const score = Number(dashboard.gk_readiness_score ?? 0);
  const meta = getReadyMeta(level);

  return (
    <section className="mt-5 rounded-2xl border border-[#ddd6ce] bg-white p-5 shadow-sm">
      <p className="text-sm font-bold text-zinc-500">골키퍼 컨디션</p>

      <div className="mt-3 rounded-3xl bg-slate-900 p-5 text-white">
        <div className="flex items-center justify-between gap-3">
          <div>
            <h2 className="text-3xl font-black">
              {meta.icon} {level}
            </h2>
            <p className="mt-2 text-base font-bold text-slate-300">
              {dashboard.gk_readiness_message ?? meta.message}
            </p>
          </div>

          <div className="text-right">
            <p className="text-xs font-bold text-slate-400">내부 지표</p>
            <p className="text-2xl font-black">{score}%</p>
          </div>
        </div>

        <div className="mt-5 h-3 overflow-hidden rounded-full bg-slate-700">
          <div
            className="h-full rounded-full bg-white"
            style={{ width: `${Math.min(Math.max(score, 0), 100)}%` }}
          />
        </div>
      </div>

      <p className="mt-4 text-sm font-bold text-zinc-500">
        숫자는 참고용입니다. 오늘 기억할 것은 {meta.icon} {level} 하나면 충분합니다.
      </p>
    </section>
  );
}

function getReadyMeta(level: string) {
  const map: Record<string, { icon: string; message: string }> = {
    ELITE: {
      icon: "🔵",
      message: "오늘은 몸 상태가 매우 좋습니다.",
    },
    READY: {
      icon: "🟢",
      message: "계획한 운동을 진행하기 좋은 상태입니다.",
    },
    NORMAL: {
      icon: "🟡",
      message: "평소 루틴을 유지하면 충분합니다.",
    },
    CARE: {
      icon: "🟠",
      message: "강도보다 회복을 함께 고려하세요.",
    },
    RECOVERY: {
      icon: "🔴",
      message: "오늘은 회복이 훈련입니다.",
    },
  };

  return map[level] ?? map.NORMAL;
}
