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
];

const CARDIO_PRESETS = [
  { label: "자전거 30분", type: "자전거", minutes: 30, kcalPerMin: 7 },
  { label: "계단 오르기 20분", type: "천국의 계단", minutes: 20, kcalPerMin: 10 },
];

const ALL_WORKOUT_KCAL = [...WORKOUT_TYPES, ...CARDIO_PRESETS.map((p) => ({ label: p.type, kcalPerMin: p.kcalPerMin }))];

// 0=일 1=월 2=화 3=수 4=목 5=금 6=토 (Bible 주간 일정 기준)
const WEEKLY_SCHEDULE = [
  { dayLabel: "회복 데이", suggestions: [] as { type: string; minutes: number }[] },
  { dayLabel: "풋살 데이", suggestions: [{ type: "풋살", minutes: 90 }] },
  {
    dayLabel: "PT 데이",
    suggestions: [
      { type: "PT", minutes: 60 },
      { type: "자전거", minutes: 20 },
      { type: "Clubbell Mobility", minutes: 15 },
    ],
  },
  { dayLabel: "풋살 데이", suggestions: [{ type: "풋살", minutes: 90 }] },
  {
    dayLabel: "PT 데이",
    suggestions: [
      { type: "PT", minutes: 60 },
      { type: "자전거", minutes: 20 },
      { type: "Clubbell Mobility", minutes: 15 },
    ],
  },
  { dayLabel: "GK Performance Day", suggestions: [{ type: "GK Performance Day", minutes: 60 }] },
  { dayLabel: "자전거 데이", suggestions: [{ type: "자전거", minutes: 50 }] },
];

function scheduleFor(dateStr: string) {
  const dayOfWeek = new Date(`${dateStr}T00:00:00`).getDay();
  return WEEKLY_SCHEDULE[dayOfWeek];
}

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
  {
    min: 95,
    label: "ELITE",
    icon: "🔵",
    text: "최상의 컨디션입니다. 적극적으로 움직여도 좋습니다.",
    bg: "bg-blue-600",
  },
  {
    min: 80,
    label: "READY",
    icon: "🟢",
    text: "오늘은 계획한 훈련을 진행하기 좋은 상태입니다.",
    bg: "bg-emerald-600",
  },
  {
    min: 60,
    label: "NORMAL",
    icon: "🟡",
    text: "오늘은 평소 루틴을 유지하면 충분합니다.",
    bg: "bg-amber-500",
  },
  {
    min: 40,
    label: "CARE",
    icon: "🟠",
    text: "오늘은 강도보다 회복을 함께 고려하세요.",
    bg: "bg-orange-600",
  },
  {
    min: 0,
    label: "RECOVERY",
    icon: "🔴",
    text: "오늘은 회복이 훈련입니다. 무리하지 않아도 괜찮습니다.",
    bg: "bg-red-600",
  },
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
  const entry = ALL_WORKOUT_KCAL.find((w) => w.label === type);
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
  const todaySchedule = useMemo(() => scheduleFor(recordDate), [recordDate]);

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

  const factors = [
    { icon: "😴", label: "수면", good: sleepHours >= 6 },
    { icon: "💧", label: "수분", good: waterLiter >= 2.5 },
    { icon: "🥩", label: "단백질", good: proteinGram >= 120 },
    { icon: "🏋", label: "운동", good: workoutDone },
    { icon: "💊", label: "복약", good: morningMed && eveningMed },
    { icon: "🙂", label: "컨디션", good: moodScore >= 4 },
  ];

  function addWorkoutItem(type: string, minutes: number) {
    setWorkoutItems((prev) => [...prev, { id: nextItemId.current++, type, minutes }]);
  }

  function updateWorkoutMinutes(id: number, minutes: number) {
    setWorkoutItems((prev) =>
      prev.map((item) => (item.id === id ? { ...item, minutes: Math.max(0, minutes) } : item))
    );
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
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-black">🧤 GK21</h1>
          <input
            type="date"
            value={recordDate}
            onChange={(e) => setRecordDate(e.target.value)}
            className="rounded-full border border-[#ddd6ce] bg-white px-4 py-2 text-sm font-bold"
          />
        </div>

        <p className="mt-2 text-sm font-bold text-zinc-500">
          🗓️ 오늘은 <span className="text-zinc-900">{todaySchedule.dayLabel}</span>입니다
        </p>

        <section
          className={[
            "mt-3 rounded-3xl p-6 text-white shadow-lg transition-colors duration-300",
            ready.level.bg,
          ].join(" ")}
        >
          <p className="text-sm font-black uppercase tracking-wide text-white/70">오늘 상태</p>
          <p className="mt-2 text-4xl font-black">
            {ready.level.icon} {ready.level.label}
          </p>
          <p className="mt-2 font-bold text-white/90">{ready.level.text}</p>

          <div className="mt-4 flex flex-wrap gap-2">
            {factors.map((f) => (
              <span
                key={f.label}
                className={[
                  "inline-flex items-center gap-1 rounded-full px-3 py-1.5 text-xs font-bold transition-colors",
                  f.good ? "bg-white text-zinc-900" : "bg-white/15 text-white/70",
                ].join(" ")}
              >
                {f.icon} {f.label}
              </span>
            ))}
          </div>
        </section>

        <Section title="⚡ 빠른 체크">
          <div className="flex flex-wrap gap-2">
            <Chip
              label="☀️ 아침약"
              active={morningMed}
              onClick={() => setMorningMed(!morningMed)}
            />
            <Chip
              label="🌙 저녁약"
              active={eveningMed}
              onClick={() => setEveningMed(!eveningMed)}
            />
            <Chip label="🍽 폭식함" active={binge} onClick={() => setBinge(!binge)} tone="warn" />
          </div>
        </Section>

        <Section title="🏋 운동">
          {todaySchedule.suggestions.length > 0 && (
            <div className="mb-3">
              <p className="mb-2 text-xs font-bold text-zinc-400">
                오늘의 추천 · {todaySchedule.dayLabel}
              </p>
              <div className="flex flex-wrap gap-2">
                {todaySchedule.suggestions.map((s) => (
                  <button
                    key={s.type}
                    type="button"
                    onClick={() => addWorkoutItem(s.type, s.minutes)}
                    className="shrink-0 rounded-full border-2 border-slate-900 bg-white px-3.5 py-2 text-sm font-bold text-slate-900 active:bg-[#f4f1ec]"
                  >
                    + {s.type} {s.minutes}분
                  </button>
                ))}
              </div>
            </div>
          )}

          <p className="mb-2 text-xs font-bold text-zinc-400">직접 추가</p>
          <div className="flex flex-wrap gap-2">
            {WORKOUT_TYPES.map((w) => (
              <button
                key={w.label}
                type="button"
                onClick={() => addWorkoutItem(w.label, 20)}
                className="shrink-0 rounded-full border border-[#ddd6ce] bg-[#faf7f2] px-3.5 py-2 text-sm font-bold active:bg-[#eee5d8]"
              >
                + {w.label}
              </button>
            ))}
          </div>

          <div className="mt-2 flex flex-wrap gap-2">
            {CARDIO_PRESETS.map((preset) => (
              <button
                key={preset.label}
                type="button"
                onClick={() => addWorkoutItem(preset.type, preset.minutes)}
                className="shrink-0 rounded-full border border-[#ddd6ce] bg-[#faf7f2] px-3.5 py-2 text-sm font-bold active:bg-[#eee5d8]"
              >
                + {preset.label}
              </button>
            ))}
          </div>

          {workoutItems.length > 0 && (
            <div className="mt-3 space-y-2">
              {workoutItems.map((item) => (
                <div key={item.id} className="flex items-center gap-2 rounded-2xl bg-[#faf7f2] p-2.5">
                  <p className="min-w-0 flex-1 truncate text-sm font-bold">{item.type}</p>

                  <Stepper
                    value={item.minutes}
                    onChange={(v) => updateWorkoutMinutes(item.id, v)}
                    suffix="분"
                  />

                  <span className="w-14 shrink-0 text-right text-xs font-bold text-zinc-500">
                    {kcalFor(item.type, item.minutes)}kcal
                  </span>

                  <button
                    type="button"
                    onClick={() => removeWorkoutItem(item.id)}
                    className="h-8 w-8 shrink-0 rounded-full bg-slate-900 text-sm font-black text-white"
                  >
                    ✕
                  </button>
                </div>
              ))}
            </div>
          )}
        </Section>

        <Section title={`🥩 단백질 · ${proteinGram}g`}>
          <div className="flex flex-wrap gap-2">
            {PROTEIN_FOODS.map((food) => (
              <Chip
                key={food.label}
                label={`${food.label} ${food.gram}g`}
                active={proteinFoods.has(food.label)}
                onClick={() => toggleProtein(food.label)}
              />
            ))}
          </div>
        </Section>

        <Section title={`💧 물 · ${waterLiter.toFixed(1)}L`}>
          <ScaleRow
            values={WATER_PRESETS}
            active={waterLiter}
            onSelect={setWaterLiter}
            format={(v) => `${v.toFixed(1)}L`}
          />
        </Section>

        <Section title={`😴 수면 · ${sleepHours}시간`}>
          <ScaleRow
            values={SLEEP_HOURS}
            active={sleepHours}
            onSelect={setSleepHours}
            format={(v) => `${v}h`}
          />
        </Section>

        <Section title="🙂 컨디션">
          <div className="grid grid-cols-5 gap-2">
            {MOOD_OPTIONS.map((mood) => (
              <button
                key={mood.score}
                type="button"
                onClick={() => setMoodScore(mood.score)}
                className={[
                  "rounded-2xl border-2 py-3 text-3xl transition-colors",
                  moodScore === mood.score
                    ? "border-slate-900 bg-slate-900"
                    : "border-[#ddd6ce] bg-[#faf7f2]",
                ].join(" ")}
              >
                {mood.icon}
              </button>
            ))}
          </div>
        </Section>

        <Section title="🏅 오늘의 한마디">
          <input
            value={mvpText}
            onChange={(e) => setMvpText(e.target.value)}
            placeholder="오늘 MVP · 가장 잘한 것 한 가지"
            className="w-full rounded-2xl border border-[#ddd6ce] bg-[#faf7f2] p-3.5 font-bold"
          />
          <textarea
            value={memo}
            onChange={(e) => setMemo(e.target.value)}
            className="mt-2 min-h-20 w-full rounded-2xl border border-[#ddd6ce] bg-[#faf7f2] p-3.5 font-bold"
            placeholder="한 줄 메모 (선택)"
          />
        </Section>

        {message && <p className="mt-3 text-center text-sm font-bold text-zinc-500">{message}</p>}

        {coachStatus !== "idle" && (
          <section className="mt-3 rounded-3xl bg-slate-900 p-6 text-white shadow-lg">
            <h2 className="text-lg font-black">🤖 AI 코치</h2>
            <p className="mt-3 font-bold leading-relaxed">
              {coachStatus === "loading" && !coachText
                ? "코치가 오늘 하루를 분석하고 있습니다..."
                : coachText}
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

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  const [icon, ...rest] = title.split(" ");
  const label = rest.join(" ");

  return (
    <section className="mt-3 rounded-3xl border border-[#ddd6ce] bg-white p-4 shadow-sm">
      <div className="mb-3 flex items-center gap-2">
        <span className="grid h-8 w-8 shrink-0 place-items-center rounded-xl bg-[#f4f1ec] text-base">
          {icon}
        </span>
        <h2 className="text-base font-black">{label}</h2>
      </div>
      {children}
    </section>
  );
}

function Chip({
  label,
  active,
  onClick,
  tone = "default",
}: {
  label: string;
  active: boolean;
  onClick: () => void;
  tone?: "default" | "warn";
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={[
        "inline-flex shrink-0 items-center gap-1.5 rounded-full border-2 px-4 py-2.5 text-sm font-bold transition-colors",
        active
          ? tone === "warn"
            ? "border-red-700 bg-red-700 text-white"
            : "border-slate-900 bg-slate-900 text-white"
          : "border-[#e5ddd0] bg-[#faf7f2] text-zinc-700",
      ].join(" ")}
    >
      {active && <span>✓</span>}
      {label}
    </button>
  );
}

function ScaleRow({
  values,
  active,
  onSelect,
  format,
}: {
  values: number[];
  active: number;
  onSelect: (value: number) => void;
  format: (value: number) => string;
}) {
  return (
    <div className="flex gap-2 overflow-x-auto pb-1">
      {values.map((value) => (
        <button
          key={value}
          type="button"
          onClick={() => onSelect(value)}
          className={[
            "shrink-0 rounded-2xl border-2 px-4 py-2.5 text-sm font-black transition-colors",
            active === value
              ? "border-slate-900 bg-slate-900 text-white"
              : "border-[#e5ddd0] bg-[#faf7f2] text-zinc-700",
          ].join(" ")}
        >
          {format(value)}
        </button>
      ))}
    </div>
  );
}

function Stepper({
  value,
  onChange,
  suffix,
}: {
  value: number;
  onChange: (value: number) => void;
  suffix: string;
}) {
  return (
    <div className="flex shrink-0 items-center gap-1.5">
      <button
        type="button"
        onClick={() => onChange(value - 5)}
        className="h-8 w-8 rounded-full border border-[#ddd6ce] bg-white text-base font-black"
      >
        −
      </button>
      <span className="w-14 text-center text-sm font-black">
        {value}
        {suffix}
      </span>
      <button
        type="button"
        onClick={() => onChange(value + 5)}
        className="h-8 w-8 rounded-full border border-[#ddd6ce] bg-white text-base font-black"
      >
        +
      </button>
    </div>
  );
}
