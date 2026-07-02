type Props = {
  ai: {
    summary?: string | null;
    cards?: {
      coach?: string | null;
    } | null;
  } | null;
};

export default function GKReadyCard({ ai }: Props) {
  const message =
    ai?.cards?.coach ??
    ai?.summary ??
    "오늘 체크를 저장하면 GK READY 코멘트가 표시됩니다.";

  return (
    <section className="mt-5 rounded-2xl border border-[#ddd6ce] bg-white p-5 shadow-sm">
      <h2 className="text-lg font-black">GK READY</h2>

      <p className="mt-4 text-zinc-600">
        {message}
      </p>
    </section>
  );
}
