type AICoach = {
  summary?: string | null;
  strength?: string | null;
  next_goal?: string | null;
  cards?: {
    coach?: string | null;
  } | null;
  recommendations?: {
    exercise?: string[] | null;
    nutrition?: string[] | null;
  } | null;
};

export default function AICoachCard({ ai }: { ai: AICoach | null }) {
  const coachMessage =
    ai?.cards?.coach ??
    ai?.summary ??
    "아직 AI 코치 분석이 없습니다. 기록 저장 후 잠시 뒤 다시 확인해주세요.";

  const strength =
    ai?.strength ??
    "오늘 기록이 쌓이면 잘한 점을 코치가 정리해드립니다.";

  const nextGoal =
    ai?.next_goal ??
    "오늘은 기록을 남긴 것만으로도 충분합니다.";

  const exercise =
    ai?.recommendations?.exercise?.slice(0, 3) ?? [
      "오늘 체크 저장",
      "수분 유지",
      "무리하지 않는 회복",
    ];

  const nutrition =
    ai?.recommendations?.nutrition?.slice(0, 3) ?? [
      "수분 기록",
      "단백질 기록",
      "폭식 여부 체크",
    ];

  return (
    <section className="mt-5 rounded-2xl border border-[#ddd6ce] bg-white p-5 shadow-sm">
      <h2 className="text-xl font-black">🤖 GK21 AI Coach</h2>

      <div className="mt-5 rounded-3xl bg-slate-900 p-6 text-white">
        <p className="text-xl font-black leading-relaxed">
          {coachMessage}
        </p>
      </div>

      <div className="mt-6 space-y-5">
        <div>
          <h3 className="font-black">🎉 오늘 잘한 점</h3>
          <p className="mt-2 leading-relaxed text-zinc-700">{strength}</p>
        </div>

        <div>
          <h3 className="font-black">🎯 다음 미션</h3>
          <p className="mt-2 leading-relaxed text-zinc-700">{nextGoal}</p>
        </div>

        <div>
          <h3 className="font-black">🏅 추천 운동</h3>
          <ul className="mt-2 list-disc space-y-1 pl-5 text-zinc-700">
            {exercise.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>

        <div>
          <h3 className="font-black">🥗 추천 식단</h3>
          <ul className="mt-2 list-disc space-y-1 pl-5 text-zinc-700">
            {nutrition.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
}
