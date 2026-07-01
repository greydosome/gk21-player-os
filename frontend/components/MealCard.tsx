type Today = {
  breakfast?: string | null;
  lunch?: string | null;
  dinner?: string | null;
  snack?: string | null;
  water_liter?: number | null;
  protein_gram?: number | null;
  binge_yn?: boolean | null;
};

type AI = {
  comments?: {
    meal?: string;
  };
};

export default function MealCard({
  today,
  ai,
}: {
  today: Today;
  ai: AI;
}) {
  return (
    <section className="mt-5 rounded-2xl border border-[#ddd6ce] bg-white p-5 shadow-sm">
      <div className="flex items-center justify-between gap-3">
        <h2 className="text-xl font-black">🍽 오늘 식단</h2>
        <span className="rounded-full bg-green-100 px-4 py-2 text-sm font-black text-green-700">
          🟢 GREEN
        </span>
      </div>

      <div className="mt-5 grid gap-3 md:grid-cols-2">
        <Info title="아침" value={today.breakfast ?? "기록 없음"} />
        <Info title="점심" value={today.lunch ?? "기록 없음"} />
        <Info title="저녁" value={today.dinner ?? "기록 없음"} />
        <Info title="간식" value={today.snack ?? "기록 없음"} />
        <Info
          title="수분"
          value={today.water_liter ? `${today.water_liter}L` : "기록 없음"}
        />
        <Info
          title="단백질"
          value={
            today.protein_gram ? `${today.protein_gram}g` : "기록 없음"
          }
        />
      </div>

      <div className="mt-5 rounded-2xl bg-[#faf7f2] p-4">
        <p className="font-black">코치 코멘트</p>
        <p className="mt-2 leading-relaxed text-zinc-700">
          {ai.comments?.meal ??
            "오늘 식단을 기록했습니다. 완벽보다 이어가는 흐름이 중요합니다."}
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
