"use client";

import { useEffect, useMemo, useRef, useState } from "react";

type WorkoutType = {
  label: string;
  kcalPerMin: number;
  defaultMinutes: number;
  subExercises?: string[];
};

const WORKOUT_TYPES: WorkoutType[] = [
  { label: "풋살", kcalPerMin: 8, defaultMinutes: 90 },
  { label: "PT", kcalPerMin: 7, defaultMinutes: 60 },
  { label: "GK Performance Day", kcalPerMin: 9, defaultMinutes: 60 },
  { label: "Clubbell Mobility", kcalPerMin: 4, defaultMinutes: 15 },
  { label: "하체모빌리티", kcalPerMin: 3, defaultMinutes: 15 },
  {
    label: "가슴운동",
    kcalPerMin: 6,
    defaultMinutes: 30,
    subExercises: ["벤치프레스", "인클라인 벤치프레스", "덤벨 플라이", "딥스", "푸시업"],
  },
  {
    label: "등운동",
    kcalPerMin: 6,
    defaultMinutes: 30,
    subExercises: ["랫풀다운", "티바로우", "데드리프트", "풀업", "시티드로우"],
  },
  {
    label: "팔운동",
    kcalPerMin: 5,
    defaultMinutes: 20,
    subExercises: ["바벨컬", "덤벨컬", "트라이셉스 익스텐션", "케이블 푸시다운", "해머컬"],
  },
  {
    label: "하체운동",
    kcalPerMin: 7,
    defaultMinutes: 30,
    subExercises: ["스쿼트", "레그프레스", "런지", "레그컬", "카프레이즈"],
  },
  {
    label: "코어운동",
    kcalPerMin: 5,
    defaultMinutes: 15,
    subExercises: ["플랭크", "크런치", "레그레이즈", "러시안트위스트", "사이드플랭크"],
  },
  { label: "자전거", kcalPerMin: 7, defaultMinutes: 30 },
  { label: "계단 오르기", kcalPerMin: 10, defaultMinutes: 20 },
];

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
  { score: 1, icon: "🤨" },
  { score: 2, icon: "🙃" },
  { score: 3, icon: "🤔" },
  { score: 4, icon: "🤓" },
  { score: 5, icon: "😎" },
];

const FALLBACK_MVP_SUGGESTIONS = [
  "오늘도 출석했다",
  "오늘도 시즌을 이어갔다",
  "작은 것 하나는 해냈다",
  "완벽하지 않아도 이어갔다",
  "오늘은 회복이 필요했다",
  "다음을 위해 오늘을 버텼다",
];

const READY_LEVELS = [
  {
    min: 90,
    label: "AWESOME",
    icon: "🔵",
    text: "오늘 정말 완벽하게 챙기고 있어요! 이 흐름 그대로 이어가세요.",
    bg: "bg-blue-600",
  },
  {
    min: 61,
    label: "GOOD",
    icon: "🟢",
    text: "좋은 흐름이에요. 계획한 훈련을 진행하기 좋은 상태입니다.",
    bg: "bg-emerald-600",
  },
  {
    min: 41,
    label: "SOSO",
    icon: "🟡",
    text: "나쁘지 않아요. 지금의 루틴을 유지하면 충분합니다.",
    bg: "bg-yellow-500",
  },
  {
    min: 21,
    label: "CARE",
    icon: "🟠",
    text: "아직 갈 길이 남았어요. 무리보다는 회복과 균형을 먼저 챙기세요.",
    bg: "bg-orange-600",
  },
  {
    min: 0,
    label: "RECOVERY",
    icon: "🔴",
    text: "지금은 회복이 우선인 시간이에요. 쉬는 것도 훈련의 일부입니다.",
    bg: "bg-red-600",
  },
];

const BLACK_LEVEL = {
  min: -1,
  label: "BREAK",
  icon: "⚫",
  text: "아직 시작 전이에요. 체크 하나만 눌러도 오늘이 시작됩니다.",
  bg: "bg-black border-2 border-zinc-700",
};

const SICK_LEVEL = {
  min: -1,
  label: "SICK DAY",
  icon: "🤒",
  text: "오늘은 아픈 날이에요. 무리하지 말고 푹 쉬는 것에 집중하세요. 컨디션 관리도 훈련의 일부입니다.",
  bg: "bg-violet-600",
};

const DEFAULT_PROTEIN_TARGET = 60;
const DEFAULT_WATER_TARGET = 2.0;
const SLEEP_TARGET = 7;

type SelectedWorkout = {
  minutes: number;
  details: Set<string>;
};

type PeriodStats = {
  days_logged: number;
  avg_sleep_hours: number | null;
  avg_water_liter: number | null;
  avg_protein_gram: number | null;
  avg_mood_score: number | null;
  workout_days: number;
  full_medication_days: number;
  binge_days: number;
  period_days: number;
};

type HistoryRow = {
  record_date: string;
  sleep_hours: number | null;
  water_liter: number | null;
  protein_gram: number | null;
  workout_done_yn: boolean | null;
  mood_score: number | null;
  binge_yn: boolean | null;
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

function round1(value: number | null) {
  return value === null || value === undefined ? "-" : Math.round(value * 10) / 10;
}

function computeReady({
  sleepHours,
  waterLiter,
  waterTarget,
  proteinGram,
  proteinTarget,
  workoutDone,
  morningMed,
  eveningMed,
  moodScore,
}: {
  sleepHours: number;
  waterLiter: number;
  waterTarget: number;
  proteinGram: number;
  proteinTarget: number;
  workoutDone: boolean;
  morningMed: boolean;
  eveningMed: boolean;
  moodScore: number | null;
}) {
  let score = 0;

  if (sleepHours >= SLEEP_TARGET) score += 20;
  else if (sleepHours >= SLEEP_TARGET - 1) score += 15;
  else if (sleepHours >= SLEEP_TARGET - 2) score += 10;
  else score += 5;

  if (waterLiter >= waterTarget) score += 20;
  else if (waterLiter >= waterTarget * 0.75) score += 15;
  else if (waterLiter >= waterTarget * 0.5) score += 10;
  else score += 5;

  if (proteinGram >= proteinTarget) score += 15;
  else if (proteinGram >= proteinTarget * 0.75) score += 10;
  else if (proteinGram >= proteinTarget * 0.5) score += 5;

  score += workoutDone ? 20 : 10;

  if (morningMed && eveningMed) score += 15;
  else if (morningMed || eveningMed) score += 8;

  if (moodScore === null) score += 0;
  else if (moodScore >= 5) score += 10;
  else if (moodScore >= 4) score += 8;
  else if (moodScore >= 3) score += 5;
  else score += 2;

  const level = READY_LEVELS.find((l) => score >= l.min) ?? READY_LEVELS[READY_LEVELS.length - 1];

  return { score, level };
}

function snapshotFormState(state: {
  morningMed: boolean;
  eveningMed: boolean;
  waterLiter: number;
  sleepHours: number;
  binge: boolean;
  isSick: boolean;
  moodScore: number | null;
  mvpText: string;
  selectedWorkouts: Map<string, SelectedWorkout>;
  proteinCounts: Map<string, number>;
}) {
  return JSON.stringify({
    morningMed: state.morningMed,
    eveningMed: state.eveningMed,
    waterLiter: state.waterLiter,
    sleepHours: state.sleepHours,
    binge: state.binge,
    isSick: state.isSick,
    moodScore: state.moodScore,
    mvpText: state.mvpText,
    workouts: Array.from(state.selectedWorkouts.entries())
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([type, w]) => [type, w.minutes, Array.from(w.details).sort()]),
    protein: Array.from(state.proteinCounts.entries())
      .filter(([, count]) => count > 0)
      .sort(([a], [b]) => a.localeCompare(b)),
  });
}

function buildMedicationNote(morning: boolean, evening: boolean) {
  if (morning && evening) return "아침약, 저녁약 복용 완료";
  if (morning && !evening) return "아침약 완료, 저녁약 체크 필요";
  if (!morning && evening) return "저녁약 완료, 아침약 체크 필요";
  return "약 체크 필요";
}

export default function Home() {
  const lastLoadedSnapshotRef = useRef<string | null>(null);
  const autoSaveTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const [recordDate, setRecordDate] = useState(today());
  const [hasRecord, setHasRecord] = useState(false);
  const [morningMed, setMorningMed] = useState(false);
  const [eveningMed, setEveningMed] = useState(false);
  const [selectedWorkouts, setSelectedWorkouts] = useState<Map<string, SelectedWorkout>>(new Map());
  const [proteinCounts, setProteinCounts] = useState<Map<string, number>>(new Map());
  const [proteinTarget, setProteinTarget] = useState(DEFAULT_PROTEIN_TARGET);
  const [waterLiter, setWaterLiter] = useState(0);
  const [waterTarget, setWaterTarget] = useState(DEFAULT_WATER_TARGET);
  const [sleepHours, setSleepHours] = useState(SLEEP_TARGET);
  const [binge, setBinge] = useState(false);
  const [isSick, setIsSick] = useState(false);
  const [moodScore, setMoodScore] = useState<number | null>(null);
  const [mvpText, setMvpText] = useState("");
  const [mvpSuggestions, setMvpSuggestions] = useState<string[]>(FALLBACK_MVP_SUGGESTIONS);
  const [mvpSuggestionsLoading, setMvpSuggestionsLoading] = useState(false);
  const [showLevelLegend, setShowLevelLegend] = useState(false);

  const [autoSaveStatus, setAutoSaveStatus] = useState<"idle" | "saving" | "saved">("idle");
  const [coachStatus, setCoachStatus] = useState<"idle" | "loading" | "ready">("idle");
  const [coachText, setCoachText] = useState("");

  const [view, setView] = useState<"today" | "week" | "month">("today");
  const [stats, setStats] = useState<PeriodStats | null>(null);
  const [history, setHistory] = useState<HistoryRow[] | null>(null);
  const [statsLoading, setStatsLoading] = useState(false);

  const proteinGram = useMemo(
    () =>
      PROTEIN_FOODS.reduce((sum, food) => sum + food.gram * (proteinCounts.get(food.label) ?? 0), 0),
    [proteinCounts]
  );

  const workoutDone = selectedWorkouts.size > 0;
  const todaySchedule = useMemo(() => scheduleFor(recordDate), [recordDate]);

  const ready = useMemo(() => {
    if (!hasRecord) return { score: 0, level: BLACK_LEVEL };
    if (isSick) return { score: 0, level: SICK_LEVEL };

    return computeReady({
      sleepHours,
      waterLiter,
      waterTarget,
      proteinGram,
      proteinTarget,
      workoutDone,
      morningMed,
      eveningMed,
      moodScore,
    });
  }, [
    hasRecord,
    isSick,
    sleepHours,
    waterLiter,
    waterTarget,
    proteinGram,
    proteinTarget,
    workoutDone,
    morningMed,
    eveningMed,
    moodScore,
  ]);

  const factors = [
    { icon: "😴", label: "수면", good: sleepHours >= SLEEP_TARGET - 1 },
    { icon: "💧", label: "수분", good: waterLiter >= waterTarget * 0.75 },
    { icon: "🥩", label: "단백질", good: proteinGram >= proteinTarget * 0.75 },
    { icon: "🏋", label: "운동", good: workoutDone },
    { icon: "💊", label: "복약", good: morningMed && eveningMed },
    { icon: "🙂", label: "컨디션", good: moodScore !== null && moodScore >= 4 },
  ];
  const missingFactors = factors.filter((f) => !f.good).map((f) => f.label);

  function toggleWorkout(type: string, defaultMinutes: number) {
    setSelectedWorkouts((prev) => {
      const next = new Map(prev);
      if (next.has(type)) next.delete(type);
      else next.set(type, { minutes: defaultMinutes, details: new Set() });
      return next;
    });
  }

  function updateWorkoutMinutes(type: string, minutes: number) {
    setSelectedWorkouts((prev) => {
      const next = new Map(prev);
      const current = next.get(type);
      if (current) next.set(type, { ...current, minutes: Math.max(0, minutes) });
      return next;
    });
  }

  function toggleWorkoutDetail(type: string, exercise: string) {
    setSelectedWorkouts((prev) => {
      const next = new Map(prev);
      const current = next.get(type);
      if (!current) return prev;
      const details = new Set(current.details);
      if (details.has(exercise)) details.delete(exercise);
      else details.add(exercise);
      next.set(type, { ...current, details });
      return next;
    });
  }

  function setProteinCount(label: string, count: number) {
    setProteinCounts((prev) => {
      const next = new Map(prev);
      next.set(label, Math.max(0, count));
      return next;
    });
  }

  function buildPayload() {
    const bikeMinutes = selectedWorkouts.get("자전거")?.minutes ?? 0;

    const completedWorkout = Array.from(selectedWorkouts.entries())
      .map(([type, w]) => {
        const detailText = w.details.size > 0 ? ` (${Array.from(w.details).join(", ")})` : "";
        return `${type} ${w.minutes}분${detailText}`;
      })
      .join(", ");

    const proteinItems = PROTEIN_FOODS.flatMap((food) =>
      Array.from({ length: proteinCounts.get(food.label) ?? 0 }, () => food.label)
    );

    return {
      record_date: recordDate,
      score: ready.score,
      grade: ready.level.label,
      mood_score: moodScore,
      memo: null,
      mvp_text: mvpText || null,
      is_sick: isSick,
      morning_med_taken: morningMed,
      evening_med_taken: eveningMed,
      medication_note: buildMedicationNote(morningMed, eveningMed),
      body: {
        water_liter: waterLiter,
        protein_gram: proteinGram,
        protein_items: proteinItems,
        binge_yn: binge,
      },
      workout: {
        planned_workout: workoutDone ? completedWorkout : null,
        completed_workout: workoutDone ? completedWorkout : null,
        bike_minutes: bikeMinutes,
        workout_done_yn: workoutDone,
      },
      workout_items: Array.from(selectedWorkouts.entries()).map(([type, w]) => ({
        workout_type: type,
        minutes: w.minutes,
        calorie_estimate: kcalFor(type, w.minutes),
        detail: w.details.size > 0 ? Array.from(w.details).join(", ") : null,
      })),
      meal: null,
      sleep: {
        sleep_hours: sleepHours,
        sleep_quality_score: sleepHours >= 7 ? 85 : 70,
        wake_condition: ready.level.label,
      },
    };
  }

  async function saveToServer() {
    const res = await fetch("/api/day", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(buildPayload()),
    });
    const data = await res.json();
    if (!res.ok || !data.success) throw new Error(JSON.stringify(data));
    return data;
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

  // 날짜가 바뀌면 그 날짜의 "오늘의 한마디" 추천 문구를 OpenAI로부터 받아온다(해당 날짜 최초 요청시 생성 후 캐시).
  useEffect(() => {
    let cancelled = false;
    setMvpSuggestionsLoading(true);

    fetch(`/api/mvp-suggestions?record_date=${recordDate}`, { cache: "no-store" })
      .then((res) => res.json())
      .then((data) => {
        if (cancelled) return;
        if (Array.isArray(data?.suggestions) && data.suggestions.length > 0) {
          setMvpSuggestions(data.suggestions);
        } else {
          setMvpSuggestions(FALLBACK_MVP_SUGGESTIONS);
        }
      })
      .catch(() => {
        if (!cancelled) setMvpSuggestions(FALLBACK_MVP_SUGGESTIONS);
      })
      .finally(() => {
        if (!cancelled) setMvpSuggestionsLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [recordDate]);

  // 날짜가 바뀌면 그 날짜의 기존 기록을 불러와서 폼을 채운다 (없으면 기본값으로 초기화).
  useEffect(() => {
    let cancelled = false;
    setCoachStatus("idle");
    setCoachText("");
    setAutoSaveStatus("idle");

    fetch(`/api/dashboard?record_date=${recordDate}`, { cache: "no-store" })
      .then((res) => res.json())
      .then((data) => {
        if (cancelled) return;

        const d = data?.dashboard;
        const detail = data?.detail;

        const loaded = {
          morningMed: d?.morning_med_taken ?? false,
          eveningMed: d?.evening_med_taken ?? false,
          waterLiter: d?.water_liter ?? 0,
          sleepHours: d?.sleep_hours ?? SLEEP_TARGET,
          binge: d?.binge_yn ?? false,
          isSick: detail?.is_sick ?? false,
          moodScore: d?.mood_score ?? null,
          mvpText: detail?.mvp_text ?? "",
        };

        const workoutMap = new Map<string, SelectedWorkout>();
        (detail?.workout_items ?? []).forEach((item: { workout_type: string; minutes: number; detail: string | null }) => {
          workoutMap.set(item.workout_type, {
            minutes: item.minutes,
            details: new Set(item.detail ? item.detail.split(", ") : []),
          });
        });

        const proteinMap = new Map<string, number>();
        (detail?.protein_items ?? []).forEach((label: string) => {
          proteinMap.set(label, (proteinMap.get(label) ?? 0) + 1);
        });

        // 자동저장 effect가 "방금 불러온 값 그대로"인 경우 저장을 건너뛸 수 있도록 스냅샷을 먼저 기록해둔다.
        lastLoadedSnapshotRef.current = snapshotFormState({
          ...loaded,
          selectedWorkouts: workoutMap,
          proteinCounts: proteinMap,
        });

        setMorningMed(loaded.morningMed);
        setEveningMed(loaded.eveningMed);
        setWaterLiter(loaded.waterLiter);
        setSleepHours(loaded.sleepHours);
        setBinge(loaded.binge);
        setIsSick(loaded.isSick);
        setMoodScore(loaded.moodScore);
        setMvpText(loaded.mvpText);
        setSelectedWorkouts(workoutMap);
        setProteinCounts(proteinMap);

        if (data?.goal?.target_protein_gram) {
          setProteinTarget(data.goal.target_protein_gram);
        }
        if (data?.goal?.target_water_liter) {
          setWaterTarget(data.goal.target_water_liter);
        }

        setHasRecord(!!d);
      });

    return () => {
      cancelled = true;
    };
  }, [recordDate]);

  // 자동 저장: 방금 불러온 값과 달라졌을 때만 2초 후 조용히 저장한다.
  useEffect(() => {
    const currentSnapshot = snapshotFormState({
      morningMed,
      eveningMed,
      waterLiter,
      sleepHours,
      binge,
      isSick,
      moodScore,
      mvpText,
      selectedWorkouts,
      proteinCounts,
    });

    if (currentSnapshot === lastLoadedSnapshotRef.current) return;

    setHasRecord(true);

    if (autoSaveTimer.current) clearTimeout(autoSaveTimer.current);

    autoSaveTimer.current = setTimeout(async () => {
      setAutoSaveStatus("saving");
      try {
        await saveToServer();
        lastLoadedSnapshotRef.current = currentSnapshot;
        setAutoSaveStatus("saved");
      } catch {
        setAutoSaveStatus("idle");
      }
    }, 2000);

    return () => {
      if (autoSaveTimer.current) clearTimeout(autoSaveTimer.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    recordDate,
    morningMed,
    eveningMed,
    selectedWorkouts,
    proteinCounts,
    waterLiter,
    sleepHours,
    binge,
    isSick,
    moodScore,
    mvpText,
  ]);

  async function requestCoaching() {
    setCoachStatus("loading");
    setCoachText("");
    if (autoSaveTimer.current) clearTimeout(autoSaveTimer.current);

    try {
      setAutoSaveStatus("saving");
      await saveToServer();
      lastLoadedSnapshotRef.current = snapshotFormState({
        morningMed,
        eveningMed,
        waterLiter,
        sleepHours,
        binge,
        isSick,
        moodScore,
        mvpText,
        selectedWorkouts,
        proteinCounts,
      });
      setAutoSaveStatus("saved");
      pollCoachFeedback(recordDate, 8);
    } catch (e) {
      setCoachStatus("idle");
      setAutoSaveStatus("idle");
      alert(`저장 실패: ${String(e)}`);
    }
  }

  useEffect(() => {
    if (view === "today") return;

    setStatsLoading(true);
    Promise.all([
      fetch(`/api/stats?period=${view}&record_date=${recordDate}`, { cache: "no-store" }).then((res) =>
        res.json()
      ),
      fetch(`/api/stats/history?period=${view}&record_date=${recordDate}`, { cache: "no-store" }).then(
        (res) => res.json()
      ),
    ])
      .then(([statsData, historyData]) => {
        setStats(statsData?.stats ?? null);
        setHistory(historyData?.history ?? null);
      })
      .finally(() => setStatsLoading(false));
  }, [view, recordDate]);

  return (
    <main className="min-h-screen bg-zinc-950 pb-32 text-zinc-100">
      <div className="mx-auto max-w-xl p-4">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-black">🧤 GK21</h1>
          <input
            type="date"
            value={recordDate}
            onChange={(e) => setRecordDate(e.target.value)}
            className="rounded-full border border-zinc-700 bg-zinc-900 px-4 py-2 text-sm font-bold text-zinc-100"
          />
        </div>

        <p className="mt-2 text-sm font-bold text-zinc-500">
          🗓️ {recordDate === today() ? "오늘은" : `${recordDate}은(는)`}{" "}
          <span className="text-zinc-100">{todaySchedule.dayLabel}</span>입니다
        </p>

        <section
          className={[
            "mt-3 rounded-3xl p-6 text-white shadow-lg transition-colors duration-300",
            ready.level.bg,
          ].join(" ")}
        >
          <p className="text-sm font-black uppercase tracking-wide text-white/70">
            {recordDate === today() ? "오늘 상태" : `${recordDate} 상태`}
          </p>
          <p className="mt-2 text-4xl font-black">
            {ready.level.icon} {ready.level.label}
          </p>
          <p className="mt-2 font-bold text-white/90">{ready.level.text}</p>

          {hasRecord && !isSick && (
            <>
              <p className="mt-2 text-sm font-bold text-white/80">
                {missingFactors.length > 0
                  ? `부족한 부분: ${missingFactors.join(", ")}`
                  : "모든 항목이 좋은 상태입니다"}
              </p>

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
            </>
          )}

          <button
            type="button"
            onClick={() => setShowLevelLegend((v) => !v)}
            className="mt-3 text-xs font-bold text-white/70 underline"
          >
            {showLevelLegend ? "등급 설명 닫기" : "등급 5단계 보기"}
          </button>

          {showLevelLegend && (
            <div className="mt-2 space-y-1.5 rounded-2xl bg-black/20 p-3">
              <p className="text-xs font-bold text-white/90">
                {BLACK_LEVEL.icon} {BLACK_LEVEL.label} (기록 없음) — {BLACK_LEVEL.text}
              </p>
              {READY_LEVELS.map((l) => (
                <p key={l.label} className="text-xs font-bold text-white/90">
                  {l.icon} {l.label} — {l.text}
                </p>
              ))}
              <p className="text-xs font-bold text-white/90">
                {SICK_LEVEL.icon} {SICK_LEVEL.label} (아픈 날 체크 시) — {SICK_LEVEL.text}
              </p>
            </div>
          )}
        </section>

        <div className="mt-3 grid grid-cols-3 gap-2">
          {(
            [
              { key: "today", label: "오늘" },
              { key: "week", label: "위클리" },
              { key: "month", label: "먼슬리" },
            ] as const
          ).map((tab) => (
            <button
              key={tab.key}
              type="button"
              onClick={() => setView(tab.key)}
              className={[
                "rounded-2xl border-2 py-2.5 text-sm font-black transition-colors",
                view === tab.key
                  ? "border-emerald-500 bg-emerald-500 text-zinc-950"
                  : "border-zinc-800 bg-zinc-900 text-zinc-400",
              ].join(" ")}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {view !== "today" ? (
          <section className="mt-3 space-y-3">
            <div className="rounded-3xl border border-zinc-800 bg-zinc-900 p-4 shadow-sm">
              <h2 className="text-base font-black text-zinc-100">
                {view === "week" ? "최근 7일" : "최근 30일"} 요약
              </h2>

              {statsLoading || !stats ? (
                <p className="mt-3 text-sm font-bold text-zinc-500">불러오는 중...</p>
              ) : (
                <div className="mt-3 grid grid-cols-2 gap-2">
                  <StatTile label="기록일" value={`${stats.days_logged}/${stats.period_days}일`} />
                  <StatTile label="운동일" value={`${stats.workout_days}일`} />
                  <StatTile label="복약 완료일" value={`${stats.full_medication_days}일`} />
                  <StatTile label="폭식일" value={`${stats.binge_days}일`} />
                </div>
              )}
            </div>

            {!statsLoading && history && (
              <>
                <TrendChart
                  title="😴 수면"
                  unit="h"
                  data={history.map((h) => h.sleep_hours)}
                  dates={history.map((h) => h.record_date)}
                />
                <TrendChart
                  title="💧 수분"
                  unit="L"
                  data={history.map((h) => h.water_liter)}
                  dates={history.map((h) => h.record_date)}
                />
                <TrendChart
                  title="🥩 단백질"
                  unit="g"
                  data={history.map((h) => h.protein_gram)}
                  dates={history.map((h) => h.record_date)}
                />
                <WorkoutDots data={history.map((h) => h.workout_done_yn)} dates={history.map((h) => h.record_date)} />
              </>
            )}
          </section>
        ) : (
          <>
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
                <Chip label="🤒 아픈 날" active={isSick} onClick={() => setIsSick(!isSick)} tone="warn" />
              </div>
            </Section>

            <Section title="🏋 운동">
              <div className="flex flex-wrap gap-2">
                {WORKOUT_TYPES.map((w) => {
                  const suggestion = todaySchedule.suggestions.find((s) => s.type === w.label);
                  const isSelected = selectedWorkouts.has(w.label);

                  return (
                    <button
                      key={w.label}
                      type="button"
                      onClick={() => toggleWorkout(w.label, suggestion?.minutes ?? w.defaultMinutes)}
                      className={[
                        "shrink-0 rounded-full border-2 px-3.5 py-2 text-sm font-bold transition-colors",
                        isSelected
                          ? "border-emerald-500 bg-emerald-500 text-zinc-950"
                          : suggestion
                            ? "border-amber-500 bg-zinc-900 text-amber-400"
                            : "border-zinc-700 bg-zinc-800 text-zinc-200",
                      ].join(" ")}
                    >
                      {isSelected ? "✓ " : suggestion ? "⭐ " : ""}
                      {w.label}
                    </button>
                  );
                })}
              </div>

              {selectedWorkouts.size > 0 && (
                <div className="mt-3 space-y-2">
                  {Array.from(selectedWorkouts.entries()).map(([type, w]) => {
                    const typeInfo = WORKOUT_TYPES.find((x) => x.label === type);
                    return (
                      <div key={type} className="rounded-2xl bg-zinc-800 p-2.5">
                        <div className="flex items-center gap-2">
                          <p className="min-w-0 flex-1 truncate text-sm font-bold text-zinc-100">{type}</p>

                          <Stepper
                            value={w.minutes}
                            onChange={(v) => updateWorkoutMinutes(type, v)}
                            suffix="분"
                            step={5}
                          />

                          <span className="w-14 shrink-0 text-right text-xs font-bold text-zinc-500">
                            {kcalFor(type, w.minutes)}kcal
                          </span>

                          <button
                            type="button"
                            onClick={() => toggleWorkout(type, w.minutes)}
                            className="h-8 w-8 shrink-0 rounded-full bg-emerald-500 text-sm font-black text-zinc-950"
                          >
                            ✕
                          </button>
                        </div>

                        {typeInfo?.subExercises && (
                          <div className="mt-2 flex flex-wrap gap-1.5">
                            {typeInfo.subExercises.map((exercise) => (
                              <button
                                key={exercise}
                                type="button"
                                onClick={() => toggleWorkoutDetail(type, exercise)}
                                className={[
                                  "shrink-0 rounded-full border px-2.5 py-1 text-xs font-bold transition-colors",
                                  w.details.has(exercise)
                                    ? "border-emerald-500 bg-emerald-500 text-zinc-950"
                                    : "border-zinc-700 bg-zinc-900 text-zinc-400",
                                ].join(" ")}
                              >
                                {w.details.has(exercise) && "✓ "}
                                {exercise}
                              </button>
                            ))}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </Section>

            <Section title={`🥩 단백질 · ${proteinGram}g / 목표 ${proteinTarget}g`}>
              <div className="space-y-2">
                {PROTEIN_FOODS.map((food) => (
                  <div
                    key={food.label}
                    className="flex items-center justify-between rounded-2xl bg-zinc-800 p-3"
                  >
                    <div>
                      <p className="font-bold text-zinc-100">{food.label}</p>
                      <p className="text-xs text-zinc-500">{food.gram}g / 1회</p>
                    </div>
                    <Stepper
                      value={proteinCounts.get(food.label) ?? 0}
                      onChange={(v) => setProteinCount(food.label, v)}
                      suffix="회"
                      step={1}
                    />
                  </div>
                ))}
              </div>
            </Section>

            <Section title={`💧 물 · ${waterLiter.toFixed(1)}L / 목표 ${waterTarget.toFixed(1)}L`}>
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
                    onClick={() => setMoodScore(moodScore === mood.score ? null : mood.score)}
                    className={[
                      "rounded-2xl border-2 py-3 text-3xl transition-colors",
                      moodScore === mood.score
                        ? "border-emerald-500 bg-zinc-800"
                        : "border-zinc-700 bg-zinc-800",
                    ].join(" ")}
                  >
                    {mood.icon}
                  </button>
                ))}
              </div>
            </Section>

            <Section title="🏅 오늘의 한마디">
              {mvpSuggestionsLoading ? (
                <p className="text-sm font-bold text-zinc-500">AI가 오늘의 문구를 준비하고 있어요...</p>
              ) : (
                <div className="flex flex-wrap gap-2">
                  {mvpSuggestions.map((phrase) => (
                    <Chip
                      key={phrase}
                      label={phrase}
                      active={mvpText === phrase}
                      onClick={() => setMvpText(mvpText === phrase ? "" : phrase)}
                    />
                  ))}
                </div>
              )}
            </Section>

            <p className="mt-3 text-center text-xs font-bold text-zinc-600">
              {autoSaveStatus === "saving" && "자동 저장 중..."}
              {autoSaveStatus === "saved" && "✓ 자동 저장됨"}
            </p>

            {coachStatus !== "idle" && (
              <section className="mt-3 rounded-3xl border border-emerald-500/30 bg-zinc-900 p-6 shadow-lg">
                <h2 className="text-lg font-black text-emerald-400">🤖 AI 코치</h2>
                <p className="mt-3 font-bold leading-relaxed text-zinc-100">
                  {coachStatus === "loading" && !coachText
                    ? "코치가 오늘 하루를 분석하고 있습니다..."
                    : coachText}
                </p>
              </section>
            )}
          </>
        )}
      </div>

      {view === "today" && (
        <div className="fixed bottom-0 left-0 right-0 z-40 bg-zinc-950/95 px-4 py-3 backdrop-blur">
          <div className="mx-auto max-w-xl">
            <button
              type="button"
              onClick={requestCoaching}
              disabled={coachStatus === "loading"}
              className="w-full rounded-2xl bg-emerald-500 py-4 text-lg font-black text-zinc-950 shadow-lg disabled:opacity-50"
            >
              {coachStatus === "loading" ? "코칭 받는 중..." : "🤖 AI 코칭 받기"}
            </button>
          </div>
        </div>
      )}
    </main>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  const [icon, ...rest] = title.split(" ");
  const label = rest.join(" ");

  return (
    <section className="mt-3 rounded-3xl border border-zinc-800 bg-zinc-900 p-4 shadow-sm">
      <div className="mb-3 flex items-center gap-2">
        <span className="grid h-8 w-8 shrink-0 place-items-center rounded-xl bg-zinc-800 text-base">
          {icon}
        </span>
        <h2 className="text-base font-black text-zinc-100">{label}</h2>
      </div>
      {children}
    </section>
  );
}

function StatTile({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl bg-zinc-800 p-3">
      <p className="text-xs font-bold text-zinc-500">{label}</p>
      <p className="mt-1 text-lg font-black text-zinc-100">{value}</p>
    </div>
  );
}

const CHART_ACCENT = "#10b981"; // emerald-500, app brand accent used as the sequential hue

function TrendChart({
  title,
  unit,
  data,
  dates,
}: {
  title: string;
  unit: string;
  data: (number | null)[];
  dates: string[];
}) {
  const width = 300;
  const height = 70;
  const padding = 6;

  const validValues = data.filter((v): v is number => v !== null && v !== undefined);
  const bestValue = validValues.length > 0 ? Math.max(...validValues) : null;
  const maxValue = Math.max(bestValue ?? 0, 1) * 1.1;
  const stepX = data.length > 1 ? (width - padding * 2) / (data.length - 1) : 0;

  const points = data.map((v, i) => {
    if (v === null || v === undefined) return null;
    const x = padding + i * stepX;
    const y = height - padding - (v / maxValue) * (height - padding * 2);
    return { x, y };
  });

  const pathParts: string[] = [];
  let drawing = false;
  points.forEach((p) => {
    if (!p) {
      drawing = false;
      return;
    }
    pathParts.push(`${drawing ? "L" : "M"} ${p.x.toFixed(1)} ${p.y.toFixed(1)}`);
    drawing = true;
  });

  const lastPoint = [...points].reverse().find((p) => p !== null) ?? null;
  const lastValue = [...validValues].pop();
  const targetY =
    bestValue !== null ? height - padding - (bestValue / maxValue) * (height - padding * 2) : null;

  return (
    <div className="rounded-2xl bg-zinc-800 p-3">
      <div className="flex items-center justify-between">
        <p className="text-xs font-bold text-zinc-400">{title}</p>
        <p className="text-sm font-black text-zinc-100">
          {lastValue !== undefined ? `${lastValue}${unit}` : "-"}
        </p>
      </div>
      <svg viewBox={`0 0 ${width} ${height}`} className="mt-2 w-full" style={{ height: 56 }}>
        {targetY !== null && (
          <line x1={padding} x2={width - padding} y1={targetY} y2={targetY} stroke="#52525b" strokeWidth="1" />
        )}
        {pathParts.length > 0 && (
          <path
            d={pathParts.join(" ")}
            fill="none"
            stroke={CHART_ACCENT}
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        )}
        {lastPoint && <circle cx={lastPoint.x} cy={lastPoint.y} r="4" fill={CHART_ACCENT} stroke="#27272a" strokeWidth="2" />}
      </svg>
      <div className="flex justify-between text-xs font-bold text-zinc-600">
        <span>{dates[0]?.slice(5)}</span>
        <span>{dates[dates.length - 1]?.slice(5)}</span>
      </div>
    </div>
  );
}

function WorkoutDots({ data, dates }: { data: (boolean | null)[]; dates: string[] }) {
  return (
    <div className="rounded-2xl bg-zinc-800 p-3">
      <p className="text-xs font-bold text-zinc-400">🏋 운동일</p>
      <div className="mt-2 flex gap-1.5">
        {data.map((done, i) => (
          <div
            key={dates[i] ?? i}
            title={dates[i]}
            className={[
              "h-6 flex-1 rounded-full",
              done === true ? "bg-emerald-500" : done === false ? "bg-zinc-700" : "bg-zinc-900",
            ].join(" ")}
          />
        ))}
      </div>
      <div className="mt-1 flex justify-between text-xs font-bold text-zinc-600">
        <span>{dates[0]?.slice(5)}</span>
        <span>{dates[dates.length - 1]?.slice(5)}</span>
      </div>
    </div>
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
            ? "border-red-600 bg-red-600 text-white"
            : "border-emerald-500 bg-emerald-500 text-zinc-950"
          : "border-zinc-700 bg-zinc-800 text-zinc-300",
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
              ? "border-emerald-500 bg-emerald-500 text-zinc-950"
              : "border-zinc-700 bg-zinc-800 text-zinc-300",
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
  step = 5,
}: {
  value: number;
  onChange: (value: number) => void;
  suffix: string;
  step?: number;
}) {
  return (
    <div className="flex shrink-0 items-center gap-1.5">
      <button
        type="button"
        onClick={() => onChange(value - step)}
        className="h-8 w-8 rounded-full border border-zinc-700 bg-zinc-900 text-base font-black text-zinc-100"
      >
        −
      </button>
      <span className="w-14 text-center text-sm font-black text-zinc-100">
        {value}
        {suffix}
      </span>
      <button
        type="button"
        onClick={() => onChange(value + step)}
        className="h-8 w-8 rounded-full border border-zinc-700 bg-zinc-900 text-base font-black text-zinc-100"
      >
        +
      </button>
    </div>
  );
}
