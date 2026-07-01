type AI = {
  summary?: string;
  strength?: string;
  next_goal?: string;
  cards?: {
    coach?: string;
    today?: string;
    week?: string;
    goal?: string;
  };
  recommendations?: {
    exercise?: string[];
    nutrition?: string[];
  };
};

export default function AICoachCard({ ai }: { ai: AI }) {
  return (
    <section className="mt-5 rounded-2xl border border-[#ddd6ce] bg-white p-5 shadow-sm">
      <h2 className="mb-5 text-xl font-black">🤖 GK21 AI Coach</h2>

      <div className="rounded-3xl bg-slate-900 p-6 text-white">
        <p className="text-xl font-black leading-relaxed">
          {ai.cards?.coach ?? ai.summary ?? "오늘도 시즌은 이어졌습니다."}
        </p>
      </div>

      <div className="mt-4 grid gap-4 md:grid-cols-2">
        <CoachBox title="🎉 오늘 잘한 점" text={ai.strength ?? ai.cards?.today} />
        <CoachBox title="🎯 내일 미션" text={ai.next_goal ?? "내일은 작은 행동 하나만 이어가면 됩니다."} />
      </div>

      <div className="mt-4 grid gap-4 md:grid-cols-2">
        <ListBox title="🥇 추천 운동" items={ai.recommendations?.exercise ?? []} />
        <ListBox title="🥗 추천 식단" items={ai.recommendations?.nutrition ?? []} />
      </div>
    </section>
  );
}

function CoachBox({ title, text }: { title: string; text?: string }) {
  return (
    <div className="rounded-2xl bg-[#faf7f2] p-4">
      <p className="font-black">{title}</p>
      <p className="mt-2 leading-relaxed text-zinc-700">
        {text ?? "좋은 흐름입니다. 오늘의 선택을 이어가면 됩니다."}
      </p>
    </div>
  );
}

function ListBox({ title, items }: { title: string; items: string[] }) {
  const displayItems = items.slice(0, 3);

  return (
    <div className="rounded-2xl bg-[#faf7f2] p-4">
      <p className="font-black">{title}</p>

      <ul className="mt-2 space-y-2 text-zinc-700">
        {displayItems.length > 0 ? (
          displayItems.map((item) => <li key={item}>• {item}</li>)
        ) : (
          <li>• 오늘은 가볍게 이어가면 됩니다.</li>
        )}
      </ul>
    </div>
  );
}
