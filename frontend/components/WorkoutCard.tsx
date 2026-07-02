type Today = {
  planned_workout?: string | null;
  completed_workout?: string | null;
  bike_minutes?: number | null;
  workout_done_yn?: boolean | null;
};

type AI = {
  comments?: {
    workout?: string;
  };
};

export default function WorkoutCard({
  today,
  ai,
}: {
  today: Today;
  ai: AI;
}) {
  return (
    <section className="mt-5 rounded-2xl border border-[#ddd6ce] bg-white p-5 shadow-sm">
      <h2 className="text-xl font-black">🏋 오늘 운동</h2>

      <div className="mt-5 grid gap-3 md:grid-cols-3">
        <Info title="계획 운동" value={today.planned_workout ?? "기록 없음"} />
        <Info title="완료 운동" value={today.completed_workout ?? "기록 없음"} />
        <Info
          title="유산소"
          value={
            today.bike_minutes
              ? `자전거 ${today.bike_minutes}분`
              : "기록 없음"
          }
        />
      </div>

      <div className="mt-5 rounded-2xl bg-[#faf7f2] p-4">
        <p className="font-black">코치 코멘트</p>
        <p className="mt-2 leading-relaxed text-zinc-700">
          {ai.comments?.workout ??
            "오늘 움직임을 기록했습니다. 작은 기록도 시즌을 이어가는 힘입니다."}
        </p>
      </div>
    </section>
  );
}

function Info({ title, value }: { title: string; value: string }) {
  return (
    <div className="rounded-2xl bg-[#faf7f2] p-4">
      <p className="text-sm font-bold text-zinc-500">{title}</p>
      <p className="mt-2 font-black">{value}</p>
    </div>
  );
}
