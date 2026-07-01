type Today = {
  morning_med_taken?: boolean | null;
  evening_med_taken?: boolean | null;
  medication_note?: string | null;
};

export default function MedicationCard({ today }: { today: Today }) {
  return (
    <section className="mt-5 rounded-2xl border border-[#ddd6ce] bg-white p-5 shadow-sm">
      <div className="flex items-center justify-between gap-3">
        <h2 className="text-xl font-black">💊 오늘 약 체크</h2>
        <span className="rounded-full bg-blue-100 px-4 py-2 text-sm font-black text-blue-700">
          컨디션 관리
        </span>
      </div>

      <div className="mt-5 grid gap-3 md:grid-cols-2">
        <MedCheck title="아침약" checked={!!today.morning_med_taken} />
        <MedCheck title="저녁약" checked={!!today.evening_med_taken} />
      </div>

      <div className="mt-5 rounded-2xl bg-[#faf7f2] p-4">
        <p className="font-black">코치 메모</p>
        <p className="mt-2 leading-relaxed text-zinc-700">
          {today.medication_note ??
            "약 복용 여부는 오늘의 컨디션을 이해하는 중요한 기록입니다. 체크만 해도 충분합니다."}
        </p>
      </div>
    </section>
  );
}

function MedCheck({
  title,
  checked,
}: {
  title: string;
  checked: boolean;
}) {
  return (
    <div className="rounded-2xl bg-[#faf7f2] p-4">
      <p className="text-sm font-bold text-zinc-500">{title}</p>
      <p className="mt-2 text-2xl font-black">
        {checked ? "✅ 복용 완료" : "⬜ 아직 체크 안 됨"}
      </p>
    </div>
  );
}
