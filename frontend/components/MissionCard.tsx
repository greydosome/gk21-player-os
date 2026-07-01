type Mission = {
  title: string;
  done: boolean;
  kind: string;
};

export default function MissionCard({ missions }: { missions: Mission[] }) {
  if (!missions || missions.length === 0) {
    return null;
  }

  return (
    <section className="mt-5 rounded-2xl border border-[#ddd6ce] bg-white p-5 shadow-sm">
      <h2 className="text-xl font-black">🎯 오늘 남은 미션</h2>

      <div className="mt-4 grid gap-3">
        {missions.map((mission) => (
          <div
            key={`${mission.kind}-${mission.title}`}
            className="flex items-center justify-between rounded-2xl bg-[#faf7f2] p-4"
          >
            <div>
              <p className="text-sm font-bold text-zinc-500">
                {labelKind(mission.kind)}
              </p>
              <p className="mt-1 text-lg font-black">{mission.title}</p>
            </div>

            <span className="text-2xl">
              {mission.done ? "✅" : "⬜"}
            </span>
          </div>
        ))}
      </div>

      <p className="mt-4 text-sm font-bold text-zinc-500">
        전부 끝내지 않아도 괜찮습니다. 오늘 한 가지라도 이어가면 충분합니다.
      </p>
    </section>
  );
}

function labelKind(kind: string) {
  const labels: Record<string, string> = {
    MED: "약",
    WATER: "수분",
    PROTEIN: "단백질",
    WORKOUT: "운동",
  };

  return labels[kind] ?? "미션";
}
