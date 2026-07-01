type Score = {
  score?: number;
  grade?: string;
  status?: string;
};

export default function ScoreCard({ score }: { score: Score }) {
  const grade = score.grade ?? "GREEN";
  return (
    <section className="mt-5 rounded-2xl border border-[#ddd6ce] bg-white p-5 shadow-sm">
      <p className="text-sm font-bold text-zinc-500">오늘의 흐름</p>
      <div className="mt-3 rounded-3xl bg-slate-900 p-6 text-white">
        <div className="text-4xl font-black">
          {gradeLabel(grade)}
        </div>
        <p className="mt-4 text-lg font-bold leading-relaxed text-slate-200">
          오늘도 시즌은 이어졌습니다. 숫자보다 중요한 건 오늘 남긴 좋은 선택입니다.
        </p>
      </div>
      <div className="mt-4 grid gap-3 md:grid-cols-3">
        <StatusPill title="운동" grade={grade} />
        <StatusPill title="식단" grade={grade} />
        <StatusPill title="회복" grade={grade} />
      </div>
    </section>
  );
}

function StatusPill({ title, grade }: { title: string; grade: string }) {
  return (
    <div className="rounded-2xl bg-[#faf7f2] p-4">
      <p className="text-sm font-bold text-zinc-500">{title}</p>
      <p className="mt-2 text-2xl font-black">{gradeLabel(grade)}</p>
    </div>
  );
}

function gradeLabel(grade: string) {
  if (grade === "GREEN") return "🟢 GREEN DAY";
  if (grade === "YELLOW") return "🟡 YELLOW DAY";
  if (grade === "RED") return "🔴 RED DAY";
  return "⚫ RESET DAY";
}
