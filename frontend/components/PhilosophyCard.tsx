type Philosophy = {
  category?: string;
  text?: string;
};

export default function PhilosophyCard({
  philosophy,
}: {
  philosophy?: Philosophy;
}) {
  if (!philosophy?.text) {
    return null;
  }

  return (
    <section className="mt-5 rounded-2xl border border-[#ddd6ce] bg-white p-5 shadow-sm">
      <p className="text-sm font-bold text-zinc-500">
        🌱 오늘의 한 문장
      </p>

      <p className="mt-3 text-xl font-black leading-relaxed text-zinc-900">
        {philosophy.text}
      </p>

      <p className="mt-3 text-xs font-bold text-zinc-400">
        {philosophy.category ?? "GK21"}
      </p>
    </section>
  );
}
