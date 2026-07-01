"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

const workoutOptions = [
  "풋살",
  "PT 상체",
  "PT 하체",
  "개인운동 어깨강화",
  "개인운동 키퍼체력",
  "유산소 자전거",
  "유산소 천국의 계단",
  "폼롤러 스트레칭",
];

export default function RecordPage() {
  const router = useRouter();
  const today = new Date().toISOString().slice(0, 10);

  const [recordDate, setRecordDate] = useState(today);
  const [morningMed, setMorningMed] = useState(false);
  const [eveningMed, setEveningMed] = useState(false);
  const [selectedWorkouts, setSelectedWorkouts] = useState<string[]>([]);
  const [customWorkout, setCustomWorkout] = useState("");
  const [bikeMinutes, setBikeMinutes] = useState("0");
  const [waterLiter, setWaterLiter] = useState("3.0");
  const [proteinGram, setProteinGram] = useState("160");
  const [sleepHours, setSleepHours] = useState("7.0");
  const [moodScore, setMoodScore] = useState(4);
  const [memo, setMemo] = useState("");
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");

  function toggleWorkout(name: string) {
    setSelectedWorkouts((prev) =>
      prev.includes(name)
        ? prev.filter((item) => item !== name)
        : [...prev, name]
    );
  }

  function addCustomWorkout() {
    const value = customWorkout.trim();

    if (!value) return;
    if (selectedWorkouts.includes(value)) return;

    setSelectedWorkouts((prev) => [...prev, value]);
    setCustomWorkout("");
  }

  async function saveRecord() {
    setSaving(true);
    setMessage("");

    const completedWorkout = selectedWorkouts.join(", ");

    const payload = {
      record_date: recordDate,
      mood_score: moodScore,
      memo,
      morning_med_taken: morningMed,
      evening_med_taken: eveningMed,
      medication_note: buildMedicationNote(morningMed, eveningMed),
      body: {
        water_liter: Number(waterLiter || 0),
        protein_gram: Number(proteinGram || 0),
        binge_yn: false,
      },
      workout: {
        planned_workout: selectedWorkouts.length > 0 ? completedWorkout : null,
        completed_workout: selectedWorkouts.length > 0 ? completedWorkout : null,
        bike_minutes: Number(bikeMinutes || 0),
        workout_done_yn:
          selectedWorkouts.length > 0 || Number(bikeMinutes || 0) > 0,
      },
      sleep: {
        sleep_hours: Number(sleepHours || 0),
        sleep_quality_score: moodScore >= 4 ? 85 : 70,
        wake_condition: moodScore >= 4 ? "GOOD" : "NORMAL",
      },
    };

    try {
      const res = await fetch("/api/day", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      const data = await res.json();

      if (!res.ok || !data.success) {
        throw new Error(JSON.stringify(data));
      }

      setMessage("저장 완료. 오늘도 Journey는 이어졌습니다.");

      setTimeout(() => {
        router.push("/");
        router.refresh();
      }, 700);
    } catch (error) {
      console.error(error);
      setMessage("저장 실패. 백엔드 API 상태를 확인해주세요.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <main className="min-h-screen bg-[#f4f1ec] pb-28 text-zinc-900">
      <div className="mx-auto max-w-md space-y-4 p-4">
        <h1 className="text-3xl font-black">📝 오늘 체크</h1>

        <section className="rounded-2xl bg-white p-5 shadow-sm">
          <p className="text-sm font-bold text-zinc-500">날짜</p>
          <input
            type="date"
            value={recordDate}
            onChange={(event) => setRecordDate(event.target.value)}
            className="mt-2 w-full rounded-xl border border-[#ddd6ce] p-3 text-lg font-bold"
          />
        </section>

        <section className="rounded-2xl bg-white p-5 shadow-sm">
          <h2 className="text-xl font-black">💊 약</h2>

          <div className="mt-4 grid grid-cols-2 gap-3">
            <ToggleButton
              label="아침약"
              active={morningMed}
              onClick={() => setMorningMed(!morningMed)}
            />
            <ToggleButton
              label="저녁약"
              active={eveningMed}
              onClick={() => setEveningMed(!eveningMed)}
            />
          </div>
        </section>

        <section className="rounded-2xl bg-white p-5 shadow-sm">
          <h2 className="text-xl font-black">🏋 운동</h2>

          <div className="mt-4 grid gap-2">
            {workoutOptions.map((name) => (
              <ToggleButton
                key={name}
                label={name}
                active={selectedWorkouts.includes(name)}
                onClick={() => toggleWorkout(name)}
              />
            ))}
          </div>

          <div className="mt-4 flex gap-2">
            <input
              value={customWorkout}
              onChange={(event) => setCustomWorkout(event.target.value)}
              placeholder="운동 직접 추가"
              className="min-w-0 flex-1 rounded-xl border border-[#ddd6ce] p-3"
            />
            <button
              type="button"
              onClick={addCustomWorkout}
              className="rounded-xl bg-slate-900 px-4 font-bold text-white"
            >
              추가
            </button>
          </div>

          <Input
            label="자전거"
            value={bikeMinutes}
            onChange={setBikeMinutes}
            suffix="분"
          />
        </section>

        <section className="rounded-2xl bg-white p-5 shadow-sm">
          <h2 className="text-xl font-black">💧 물</h2>
          <Input
            label="수분"
            value={waterLiter}
            onChange={setWaterLiter}
            suffix="L"
          />
        </section>

        <section className="rounded-2xl bg-white p-5 shadow-sm">
          <h2 className="text-xl font-black">🥩 단백질</h2>
          <Input
            label="단백질"
            value={proteinGram}
            onChange={setProteinGram}
            suffix="g"
          />
        </section>

        <section className="rounded-2xl bg-white p-5 shadow-sm">
          <h2 className="text-xl font-black">😴 수면</h2>
          <Input
            label="수면"
            value={sleepHours}
            onChange={setSleepHours}
            suffix="시간"
          />
        </section>

        <section className="rounded-2xl bg-white p-5 shadow-sm">
          <h2 className="text-xl font-black">😊 오늘 기분</h2>

          <div className="mt-4 grid grid-cols-5 gap-2 text-2xl">
            {[5, 4, 3, 2, 1].map((score) => (
              <button
                key={score}
                type="button"
                onClick={() => setMoodScore(score)}
                className={[
                  "rounded-2xl border p-3",
                  moodScore === score
                    ? "border-slate-900 bg-slate-900 text-white"
                    : "border-[#ddd6ce] bg-[#faf7f2]",
                ].join(" ")}
              >
                {moodIcon(score)}
              </button>
            ))}
          </div>
        </section>

        <section className="rounded-2xl bg-white p-5 shadow-sm">
          <h2 className="text-xl font-black">📝 메모</h2>

          <textarea
            rows={4}
            value={memo}
            onChange={(event) => setMemo(event.target.value)}
            className="mt-4 w-full rounded-xl border border-[#ddd6ce] p-3"
            placeholder="오늘 한 줄만 남겨도 충분합니다."
          />
        </section>

        {message && (
          <p className="rounded-2xl bg-white p-4 text-center font-bold text-zinc-700 shadow-sm">
            {message}
          </p>
        )}

        <button
          type="button"
          onClick={saveRecord}
          disabled={saving}
          className="w-full rounded-2xl bg-slate-900 py-4 text-lg font-bold text-white disabled:opacity-50"
        >
          {saving ? "저장 중..." : "저장하기"}
        </button>
      </div>
    </main>
  );
}

function ToggleButton({
  label,
  active,
  onClick,
}: {
  label: string;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={[
        "rounded-2xl border p-4 text-left text-base font-black",
        active
          ? "border-slate-900 bg-slate-900 text-white"
          : "border-[#ddd6ce] bg-[#faf7f2] text-zinc-900",
      ].join(" ")}
    >
      {active ? "✅ " : "⬜ "}
      {label}
    </button>
  );
}

function Input({
  label,
  value,
  onChange,
  suffix,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  suffix: string;
}) {
  return (
    <label className="mt-4 block">
      <p className="mb-2 text-sm font-bold text-zinc-500">{label}</p>
      <div className="flex items-center gap-2">
        <input
          type="number"
          value={value}
          onChange={(event) => onChange(event.target.value)}
          className="w-full rounded-xl border border-[#ddd6ce] p-3 text-lg font-bold"
        />
        <span className="font-bold text-zinc-500">{suffix}</span>
      </div>
    </label>
  );
}

function moodIcon(score: number) {
  const icons: Record<number, string> = {
    5: "😀",
    4: "🙂",
    3: "😐",
    2: "😔",
    1: "😢",
  };

  return icons[score] ?? "😐";
}

function buildMedicationNote(morning: boolean, evening: boolean) {
  if (morning && evening) return "아침약, 저녁약 복용 완료";
  if (morning && !evening) return "아침약 완료, 저녁약 체크 필요";
  if (!morning && evening) return "저녁약 완료, 아침약 체크 필요";
  return "약 체크 필요";
}
