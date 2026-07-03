"use client";

import { useMemo, useState } from "react";

const readyLevels = [
  { label: "ELITE", icon: "🔵", score: 100, text: "최상의 컨디션" },
  { label: "READY", icon: "🟢", score: 90, text: "계획대로 수행" },
  { label: "NORMAL", icon: "🟡", score: 75, text: "무난하게 이어감" },
  { label: "CARE", icon: "🟠", score: 60, text: "관리 필요" },
  { label: "RECOVERY", icon: "🔴", score: 40, text: "회복 우선" },
];

function today() {
  const now = new Date();
  const offset = now.getTimezoneOffset() * 60000;
  return new Date(now.getTime() - offset).toISOString().slice(0, 10);
}

export default function Home() {
  const [recordDate, setRecordDate] = useState(today());
  const [morningMed, setMorningMed] = useState(false);
  const [eveningMed, setEveningMed] = useState(false);
  const [workoutDone, setWorkoutDone] = useState(false);
  const [waterDone, setWaterDone] = useState(false);
  const [proteinDone, setProteinDone] = useState(false);
  const [sleepDone, setSleepDone] = useState(false);
  const [memo, setMemo] = useState("");
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");

  const score = useMemo(() => {
    let value = 0;
    if (morningMed) value += 10;
    if (eveningMed) value += 10;
    if (workoutDone) value += 20;
    if (waterDone) value += 20;
    if (proteinDone) value += 20;
    if (sleepDone) value += 20;
    return value;
  }, [morningMed, eveningMed, workoutDone, waterDone, proteinDone, sleepDone]);

  const level = useMemo(() => {
    if (score >= 100) return readyLevels[0];
    if (score >= 90) return readyLevels[1];
    if (score >= 75) return readyLevels[2];
    if (score >= 60) return readyLevels[3];
    return readyLevels[4];
  }, [score]);

  async function save() {
    setSaving(true);
    setMessage("");

    const payload = {
      record_date: recordDate,
      score,
      grade: level.label,
      mood_score: score >= 90 ? 5 : score >= 75 ? 4 : score >= 60 ? 3 : 2,
      memo,
      morning_med_taken: morningMed,
      evening_med_taken: eveningMed,
      medication_note: buildMedicationNote(morningMed, eveningMed),
      body: {
        water_liter: waterDone ? 2.5 : 0,
        protein_gram: proteinDone ? 100 : 0,
        binge_yn: false,
      },
      workout: {
        planned_workout: workoutDone ? "오늘 운동" : null,
        completed_workout: workoutDone ? "오늘 운동 완료" : null,
        bike_minutes: 0,
        workout_done_yn: workoutDone,
      },
      meal: null,
      sleep: {
        sleep_hours: sleepDone ? 7 : 0,
        sleep_quality_score: sleepDone ? 85 : 50,
        wake_condition: level.label,
      },
    };

    try {
      const res = await fetch("/api/day", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(payload),
      });

      const data = await res.json();

      if (!res.ok || !data.success) {
        setMessage(`저장 실패: ${JSON.stringify(data)}`);
        return;
      }

      setMessage("저장 완료. 오늘도 Journey는 이어졌습니다.");
    } catch (e) {
      setMessage(`저장 실패: ${String(e)}`);
    } finally {
      setSaving(false);
    }
  }

  return (
    <main className="min-h-screen bg-[#f4f1ec] pb-32 text-zinc-900">
      <div className="mx-auto max-w-xl p-4">
        <header className="rounded-3xl bg-slate-900 p-6 text-white shadow-lg">
          <h1 className="text-3xl font-black">🧤 GK21 Player OS</h1>
          <p className="mt-2 font-bold text-slate-300">
            오늘 체크 · 자동 READY · 저장
          </p>
        </header>

        <section className="mt-4 rounded-3xl border border-[#ddd6ce] bg-white p-6 shadow-sm">
          <p className="text-sm font-black text-zinc-500">오늘 상태</p>
          <div className="mt-3 flex items-center justify-between">
            <div>
              <p className="text-4xl font-black">
                {level.icon} {level.label}
              </p>
              <p className="mt-1 font-bold text-zinc-500">{level.text}</p>
            </div>
            <p className="text-4xl font-black">{score}</p>
          </div>
        </section>

        <section className="mt-4 rounded-3xl border border-[#ddd6ce] bg-white p-5 shadow-sm">
          <p className="text-sm font-black text-zinc-500">날짜</p>
          <input
            type="date"
            value={recordDate}
            onChange={(e) => setRecordDate(e.target.value)}
            className="mt-2 w-full rounded-2xl border border-[#ddd6ce] p-4 text-lg font-black"
          />
        </section>

        <section className="mt-4 rounded-3xl border border-[#ddd6ce] bg-white p-5 shadow-sm">
          <h2 className="text-xl font-black">오늘 체크</h2>

          <div className="mt-4 grid gap-3">
            <Toggle label="☀️ 아침약" active={morningMed} onClick={() => setMorningMed(!morningMed)} />
            <Toggle label="🌙 저녁약" active={eveningMed} onClick={() => setEveningMed(!eveningMed)} />
            <Toggle label="🏋 운동 완료" active={workoutDone} onClick={() => setWorkoutDone(!workoutDone)} />
            <Toggle label="💧 수분 2.5L" active={waterDone} onClick={() => setWaterDone(!waterDone)} />
            <Toggle label="🥩 단백질 100g" active={proteinDone} onClick={() => setProteinDone(!proteinDone)} />
            <Toggle label="😴 수면 7h" active={sleepDone} onClick={() => setSleepDone(!sleepDone)} />
          </div>
        </section>

        <section className="mt-4 rounded-3xl border border-[#ddd6ce] bg-white p-5 shadow-sm">
          <h2 className="text-xl font-black">📝 한 줄 메모</h2>
          <textarea
            value={memo}
            onChange={(e) => setMemo(e.target.value)}
            className="mt-3 min-h-28 w-full rounded-2xl border border-[#ddd6ce] p-4 font-bold"
            placeholder="오늘 한 줄만 남겨도 충분합니다."
          />
        </section>

        {message && (
          <p className="mt-4 rounded-2xl bg-white p-4 text-center font-black shadow-sm">
            {message}
          </p>
        )}
      </div>

      <div className="fixed bottom-20 left-0 right-0 z-40 bg-[#f4f1ec]/95 px-4 py-3 backdrop-blur">
        <div className="mx-auto max-w-xl">
          <button
            type="button"
            onClick={save}
            disabled={saving}
            className="w-full rounded-2xl bg-slate-900 py-4 text-lg font-black text-white shadow-lg disabled:opacity-50"
          >
            {saving ? "저장 중..." : "저장하기"}
          </button>
        </div>
      </div>
    </main>
  );
}

function Toggle({label, active, onClick}: {label: string; active: boolean; onClick: () => void}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={[
        "rounded-2xl border p-4 text-left text-lg font-black",
        active
          ? "border-slate-900 bg-slate-900 text-white"
          : "border-[#ddd6ce] bg-[#faf7f2] text-zinc-900",
      ].join(" ")}
    >
      {active ? "✅ " : "⬜ "} {label}
    </button>
  );
}

function buildMedicationNote(morning: boolean, evening: boolean) {
  if (morning && evening) return "아침약, 저녁약 복용 완료";
  if (morning && !evening) return "아침약 완료, 저녁약 체크 필요";
  if (!morning && evening) return "저녁약 완료, 아침약 체크 필요";
  return "약 체크 필요";
}
