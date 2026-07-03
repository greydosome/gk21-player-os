"use client";

import { useMemo, useRef, useState } from "react";

const WORKOUT_TYPES: { label: string; kcalPerMin: number }[] = [
  { label: "풋살", kcalPerMin: 8 },
  { label: "PT", kcalPerMin: 7 },
  { label: "GK Performance Day", kcalPerMin: 9 },
  { label: "Clubbell Mobility", kcalPerMin: 4 },
  { label: "하체모빌리티", kcalPerMin: 3 },
  { label: "가슴운동", kcalPerMin: 6 },
  { label: "등운동", kcalPerMin: 6 },
  { label: "팔운동", kcalPerMin: 5 },
  { label: "하체운동", kcalPerMin: 7 },
  { label: "자전거", kcalPerMin: 7 },
  { label: "천국의 계단", kcalPerMin: 10 },
];

const CARDIO_PRESETS = [
  { label: "🚴 자전거 30분", type: "자전거", minutes: 30 },
  { label: "🪜 천국의 계단 20분", type: "천국의 계단", minutes: 20 },
];

const PROTEIN_FOODS: { label: string; gram: number }[] = [
  { label: "참치", gram: 25 },
  { label: "닭가슴살", gram: 25 },
  { label: "달걀", gram: 6 },
  { label: "그릭요거트", gram: 10 },
];

const WATER_PRESETS = [0, 0.3, 0.5, 0.8, 1.0, 1.3, 1.5, 1.8, 2.0, 2.3, 2.5, 3.0];

const SLEEP_HOURS = Array.from({ length: 24 }, (_, i) => i + 1);

const MOOD_OPTIONS = [
  { score: 5, icon: "😀" },
  { score: 4, icon: "🙂" },
  { score: 3, icon: "😐" },
  { score: 2, icon: "😔" },
  { score: 1, icon: "😢" },
];

const READY_LEVELS = [
  { min: 95, label: "ELITE", icon: "🔵", text: "최상의 컨디션입니다. 적극적으로 움직여도 좋습니다." },
  { min: 80, label: "READY", icon: "🟢", text: "오늘은 계획한 훈련을 진행하기 좋은 상태입니다." },
  { min: 60, label: "NORMAL", icon: "🟡", text: "오늘은 평소 루틴을 유지하면 충분합니다." },
  { min: 40, label: "CARE", icon: "🟠", text: "오늘은 강도보다 회복을 함께 고려하세요." },
  { min: 0, label: "RECOVERY", icon: "🔴", text: "오늘은 회복이 훈련입니다. 무리하지 않아도 괜찮습니다." },
];

type WorkoutItem = {
  id: number;
  type: string;
  minutes: number;
};

function today() {
  const now = new Date();
  const offset = now.getTimezoneOffset() * 60000;
  return new Date(now.getTime() - offset).toISOString().slice(0, 10);
}

function kcalFor(type: string, minutes: number) {
  const entry = WORKOUT_TYPES.find((w) => w.label === type);
  return Math.round((entry?.kcalPerMin ?? 6) * minutes);
}

function computeReady({
  sleepHours,
  waterLiter,
  proteinGram,
  workoutDone,
  morningMed,
  eveningMed,
  moodScore,
}: {
  sleepHours: number;
  waterLiter: number;
  proteinGram: number;
  workoutDone: boolean;
  morningMed: boolean;
  eveningMed: boolean;
  moodScore: number;
}) {
  let score = 0;

  if (sleepHours >= 7) score += 20;
  else if (sleepHours >= 6) score += 15;
  else if (sleepHours >= 5) score += 10;
  else score += 5;

  if (waterLiter >= 3.0) score += 20;
  else if (waterLiter >= 2.5) score += 15;
  else if (waterLiter >= 2.0) score += 10;
  else score += 5;

  if (proteinGram >= 160) score += 15;
  else if (proteinGram >= 120) score += 10;
  else if (proteinGram >= 80) score += 5;

  score += workoutDone ? 20 : 10;

  if (morningMed && eveningMed) score += 15;
  else if (morningMed || eveningMed) score += 8;

  if (moodScore >= 5) score += 10;
  else if (moodScore >= 4) score += 8;
  else if (moodScore >= 3) score += 5;
  else score += 2;

  const level = READY_LEVELS.find((l) => score >= l.min) ?? READY_LEVELS[READY_LEVELS.length - 1];

  return { score, level };
}

function buildMedicationNote(morning: boolean, evening: boolean) {
  if (morning && evening) return "아침약, 저녁약 복용 완료";
  if (morning && !evening) return "아침약 완료, 저녁약 체크 필요";
  if (!morning && evening) return "저녁약 완료, 아침약 체크 필요";
  return "약 체크 필요";
}

export default function Home() {
  const nextItemId = useRef(1);

  const [recordDate, setRecordDate] = useState(today());
  const [morningMed, setMorningMed] = useState(false);
  const [eveningMed, setEveningMed] = useState(false);
  const [workoutItems, setWorkoutItems] = useState<WorkoutItem[]>([]);
  const [proteinFoods, setProteinFoods] = useState<Set<string>>(new Set());
  const [waterLiter, setWaterLiter] = useState(0);
  const [sleepHours, setSleepHours] = useState(7);
  const [binge, setBinge] = useState(false);
  const [moodScore, setMoodScore] = useState(4);
  const [mvpText, setMvpText] = useState("");
  const [memo, setMemo] = useState("");

  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");
  const [coachStatus, setCoachStatus] = useState<"idle" | "loading" | "ready">("idle");
  const [coachText, setCoachText] = useState("");

  const proteinGram = useMemo(
    () =>
      PROTEIN_FOODS.filter((food) => proteinFoods.has(food.label)).reduce(
        (sum, food) => sum + food.gram,
        0
      ),
    [proteinFoods]
  );

  const workoutDone = workoutItems.length > 0;

  const ready = useMemo(
    () =>
      computeReady({
        sleepHours,
        waterLiter,
        proteinGram,
        workoutDone,
        morningMed,
        eveningMed,
        moodScore,
      }),
    [sleepHours, waterLiter, proteinGram, workoutDone, morningMed, eveningMed, moodScore]
  );

  function addWorkoutItem(type: string, minutes: number) {
    setWorkoutItems((prev) => [...prev, { id: nextItemId.current++, type, minutes }]);
  }

  function updateWorkoutMinutes(id: number, minutes: number) {
    setWorkoutItems((prev) => prev.map((item) => (item.id === id ? { ...item, minutes } : item)));
  }

  function removeWorkoutItem(id: number) {
    setWorkoutItems((prev) => prev.filter((item) => item.id !== id));
  }

  function toggleProtein(label: string) {
    setProteinFoods((prev) => {
      const next = new Set(prev);
      if (next.has(label)) next.delete(label);
      else next.add(label);
      return next;
    });
  }

  async function pollCoachFeedback(date: string, attemptsLeft: number) {
    try {
      const res = await fetch(`/api/dashboard?record_date=${date}`, { cache: "no-store" });
      const data = await res.json();
      const ai = data?.ai;
      const text = ai?.cards?.coach ?? ai?.summary;

      if (text) setCoachText(text);

      if (ai?.overview?.status === "COMPLETED" || attemptsLeft <= 0) {
        setCoachStatus("ready");
        return;
      }

      setTimeout(() => pollCoachFeedback(date, attemptsLeft - 1), 3000);
    } catch {
      setCoachStatus("ready");
    }
  }

  async function save() {
    setSaving(true);
    setMessage("");
    setCoachStatus("loading");
    setCoachText("");

    const bikeMinutes = workoutItems
      .filter((item) => item.type === "자전거")
      .reduce((sum, item) => sum + item.minutes, 0);

    const completedWorkout = workoutItems.map((item) => `${item.type} ${item.minutes}분`).join(", ");

    const payload = {
      record_date: recordDate,
      score: ready.score,
      grade: ready.level.label,
      mood_score: moodScore,
      memo,
      mvp_text: mvpText || null,
      morning_med_taken: morningMed,
      evening_med_taken: eveningMed,
      medication_note: buildMedicationNote(morningMed, eveningMed),
      body: {
        water_liter: waterLiter,
        protein_gram: proteinGram,
        protein_items: Array.from(proteinFoods),
        binge_yn: binge,
      },
      workout: {
        planned_workout: workoutDone ? completedWorkout : null,
        completed_workout: workoutDone ? completedWorkout : null,
        bike_minutes: bikeMinutes,
        workout_done_yn: workoutDone,
      },
      workout_items: workoutItems.map((item) => ({
        workout_type: item.type,
        minutes: item.minutes,
        calorie_estimate: kcalFor(item.type, item.minutes),
      })),
      meal: null,
      sleep: {
        sleep_hours: sleepHours,
        sleep_quality_score: sleepHours >= 7 ? 85 : 70,
        wake_condition: ready.level.label,
      },
    };

    try {
      const res = await fetch("/api/day", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const data = await res.json();

      if (!res.ok || !data.success) {
        setMessage(`저장 실패: ${JSON.stringify(data)}`);
        setCoachStatus("idle");
        return;
      }

      setMessage("저장 완료. 오늘도 Journey는 이어졌습니다.");
      pollCoachFeedback(recordDate, 8);
    } catch (e) {
      setMessage(`저장 실패: ${String(e)}`);
      setCoachStatus("idle");
    } finally {
      setSaving(false);
    }
  }

  return (
    <main className="min-h-screen bg-[#f4f1ec] pb-32 text-zinc-900">
      <div className="mx-auto max-w-xl p-4">
        <header className="rounded-3xl bg-slate-900 p-6 text-white shadow-lg">
          <h1 className="text-3xl font-black">🧤 GK21 Player OS</h1>
          <p className="mt-2 font-bold text-slate-300">오늘 체크 · 자동 READY · 저장</p>
        </header>

        <section className="mt-4 rounded-3xl border border-[#ddd6ce] bg-white p-6 shadow-sm">
          <p className="text-sm font-black text-zinc-500">오늘 상태</p>
          <p className="mt-3 text-4xl font-black">
            {ready.level.icon} {ready.level.label}
          </p>
          <p className="mt-2 font-bold text-zinc-500">{ready.level.text}</p>
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
          <h2 className="text-xl font-black">💊 약</h2>
          <div className="mt-4 grid grid-cols-2 gap-3">
            <Toggle label="☀️ 아침약" active={morningMed} onClick={() => setMorningMed(!morningMed)} />
            <Toggle label="🌙 저녁약" active={eveningMed} onClick={() => setEveningMed(!eveningMed)} />
          </div>
        </section>

        <section className="mt-4 rounded-3xl border border-[#ddd6ce] bg-white p-5 shadow-sm">
          <h2 className="text-xl font-black">🏋 운동</h2>

          <div className="mt-4 flex flex-wrap gap-2">
            {WORKOUT_TYPES.map((w) => (
              <button
                key={w.label}
                type="button"
                onClick={() => addWorkoutItem(w.label, 20)}
                className="rounded-full border border-[#ddd6ce] bg-[#faf7f2] px-4 py-2 text-sm font-bold"
              >
                + {w.label}
              </button>
            ))}
          </div>

          <div className="mt-3 flex flex-wrap gap-2">
            {CARDIO_PRESETS.map((preset) => (
              <button
                key={preset.label}
                type="button"
                onClick={() => addWorkoutItem(preset.type, preset.minutes)}
                className="rounded-full border border-slate-900 bg-slate-900 px-4 py-2 text-sm font-bold text-white"
              >
                {preset.label}
              </button>
            ))}
          </div>

          {workoutItems.length > 0 && (
            <div className="mt-4 space-y-2">
              {workoutItems.map((item) => (
                <div
                  key={item.id}
                  className="flex items-center gap-2 rounded-2xl bg-[#faf7f2] p-3"
                >
                  <p className="flex-1 font-bold">{item.type}</p>
                  <input
                    type="number"
                    value={item.minutes}
                    onChange={(e) => updateWorkoutMinutes(item.id, Number(e.target.value || 0))}
                    className="w-16 rounded-xl border border-[#ddd6ce] p-2 text-center font-bold"
                  />
                  <span className="text-sm font-bold text-zinc-500">분</span>
                  <span className="w-16 text-right text-sm font-bold text-zinc-500">
                    {kcalFor(item.type, item.minutes)}kcal
                  </span>
                  <button
                    type="button"
                    onClick={() => removeWorkoutItem(item.id)}
                    className="rounded-full bg-slate-900 px-3 py-1 text-sm font-bold text-white"
                  >
                    ✕
                  </button>
                </div>
              ))}
            </div>
          )}
        </section>

        <section className="mt-4 rounded-3xl border border-[#ddd6ce] bg-white p-5 shadow-sm">
          <h2 className="text-xl font-black">🥩 단백질</h2>
          <div className="mt-4 grid grid-cols-2 gap-3">
            {PROTEIN_FOODS.map((food) => (
              <Toggle
                key={food.label}
                label={`${food.label} (${food.gram}g)`}
                active={proteinFoods.has(food.label)}
                onClick={() => toggleProtein(food.label)}
              />
            ))}
          </div>
          <p className="mt-3 text-sm font-bold text-zinc-500">오늘 합계: {proteinGram}g</p>
        </section>

        <section className="mt-4 rounded-3xl border border-[#ddd6ce] bg-white p-5 shadow-sm">
          <h2 className="text-xl font-black">💧 물</h2>
          <div className="mt-4 flex gap-2 overflow-x-auto pb-1">
            {WATER_PRESETS.map((liter) => (
              <button
                key={liter}
                type="button"
                onClick={() => setWaterLiter(liter)}
                className={[
                  "shrink-0 rounded-2xl border px-4 py-3 font-black",
                  waterLiter === liter
                    ? "border-slate-900 bg-slate-900 text-white"
                    : "border-[#ddd6ce] bg-[#faf7f2]",
                ].join(" ")}
              >
                {liter.toFixed(1)}L
              </button>
            ))}
          </div>
        </section>

        <section className="mt-4 rounded-3xl border border-[#ddd6ce] bg-white p-5 shadow-sm">
          <h2 className="text-xl font-black">😴 수면</h2>
          <div className="mt-4 flex gap-2 overflow-x-auto pb-1">
            {SLEEP_HOURS.map((hour) => (
              <button
                key={hour}
                type="button"
                onClick={() => setSleepHours(hour)}
                className={[
                  "shrink-0 rounded-2xl border px-4 py-3 font-black",
                  sleepHours === hour
                    ? "border-slate-900 bg-slate-900 text-white"
                    : "border-[#ddd6ce] bg-[#faf7f2]",
                ].join(" ")}
              >
                {hour}h
              </button>
            ))}
          </div>
        </section>

        <section className="mt-4 rounded-3xl border border-[#ddd6ce] bg-white p-5 shadow-sm">
          <h2 className="text-xl font-black">🍽 폭식</h2>
          <label className="mt-4 flex items-center gap-3 font-bold">
            <input
              type="checkbox"
              checked={binge}
              onChange={(e) => setBinge(e.target.checked)}
              className="h-6 w-6 accent-slate-900"
            />
            오늘 밤 폭식했다
          </label>
        </section>

        <section className="mt-4 rounded-3xl border border-[#ddd6ce] bg-white p-5 shadow-sm">
          <h2 className="text-xl font-black">🙂 컨디션</h2>
          <div className="mt-4 grid grid-cols-5 gap-2 text-2xl">
            {MOOD_OPTIONS.map((mood) => (
              <button
                key={mood.score}
                type="button"
                onClick={() => setMoodScore(mood.score)}
                className={[
                  "rounded-2xl border p-3",
                  moodScore === mood.score
                    ? "border-slate-900 bg-slate-900 text-white"
                    : "border-[#ddd6ce] bg-[#faf7f2]",
                ].join(" ")}
              >
                {mood.icon}
              </button>
            ))}
          </div>
        </section>

        <section className="mt-4 rounded-3xl border border-[#ddd6ce] bg-white p-5 shadow-sm">
          <h2 className="text-xl font-black">🏅 오늘 MVP</h2>
          <input
            value={mvpText}
            onChange={(e) => setMvpText(e.target.value)}
            placeholder="오늘 가장 잘한 것 한 가지"
            className="mt-3 w-full rounded-2xl border border-[#ddd6ce] p-4 font-bold"
          />
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
          <p className="mt-4 rounded-2xl bg-white p-4 text-center font-black shadow-sm">{message}</p>
        )}

        {coachStatus !== "idle" && (
          <section className="mt-4 rounded-3xl bg-slate-900 p-6 text-white shadow-lg">
            <h2 className="text-lg font-black">🤖 AI 코치</h2>
            <p className="mt-3 font-bold leading-relaxed">
              {coachStatus === "loading" && !coachText ? "코치가 오늘 하루를 분석하고 있습니다..." : coachText}
            </p>
          </section>
        )}
      </div>

      <div className="fixed bottom-0 left-0 right-0 z-40 bg-[#f4f1ec]/95 px-4 py-3 backdrop-blur">
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

function Toggle({ label, active, onClick }: { label: string; active: boolean; onClick: () => void }) {
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
