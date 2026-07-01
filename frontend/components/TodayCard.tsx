type Today = {
  day_no: number;
  week_no: number;
  record_date: string;
  mood_score?: number;
  planned_workout?: string;
};

export default function TodayCard({ today }: { today: Today }) {
  return (
    <section className="mt-5 rounded-2xl border border-[#ddd6ce] bg-white p-5 shadow-sm">
      <h2 className="mb-5 text-xl font-black tracking-tight">📅 오늘 기록</h2>

      <div className="grid gap-3 md:grid-cols-3">
        <InfoField label="DAY" value={String(today.day_no)} />
        <InfoField label="WEEK" value={String(today.week_no)} />
        <InfoField label="날짜" value={today.record_date} />
      </div>

      <div className="mt-5">
        <p className="text-sm font-bold text-zinc-500">컨디션</p>
        <div className="mt-2 rounded-xl border border-[#ddd6ce] bg-zinc-100 p-3 text-xl">
          {today.mood_score === 5 ? "😄" : "🙂"}
        </div>
      </div>

      <div className="mt-5">
        <p className="text-sm font-bold text-zinc-500">오늘 예정</p>
        <div className="mt-2 rounded-xl border border-[#ddd6ce] bg-white p-3 text-zinc-900">
          {today.planned_workout ?? "예정 운동 없음"}
        </div>
      </div>
    </section>
  );
}

function InfoField({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-sm font-bold text-zinc-500">{label}</p>
      <div className="mt-1 rounded-xl border border-[#ddd6ce] bg-zinc-100 p-3 text-zinc-900">
        {value}
      </div>
    </div>
  );
}
