"use client";

import { memo, useCallback, useEffect, useMemo, useRef, useState } from "react";

type WorkoutType = {
  label: string;
  category: "strength" | "cardio";
  kcalPerMin: number;
  defaultMinutes: number;
  subExercises?: string[];
};

const WORKOUT_TYPES: WorkoutType[] = [
  { label: "풋살", category: "cardio", kcalPerMin: 8, defaultMinutes: 90 },
  { label: "PT", category: "strength", kcalPerMin: 7, defaultMinutes: 60 },
  {
    label: "GK Performance Day",
    category: "cardio",
    kcalPerMin: 9,
    defaultMinutes: 60,
    subExercises: ["다이빙 세이브", "캐칭 훈련", "1대1 대응", "크로스 캐칭", "반응 훈련", "슈팅 스톱"],
  },
  {
    label: "Clubbell Mobility",
    category: "strength",
    kcalPerMin: 4,
    defaultMinutes: 15,
    subExercises: ["숄더 캐스트", "밀", "스위치", "프라이멀 스윙", "180 스윙", "숄더 스윙"],
  },
  {
    label: "하체모빌리티",
    category: "strength",
    kcalPerMin: 3,
    defaultMinutes: 15,
    subExercises: ["힙 서클", "90/90 스트레치", "카프 스트레치", "월드 그레이티스트 스트레치", "폼롤러", "런지 스트레치", "발목 모빌리티"],
  },
  {
    label: "가슴운동",
    category: "strength",
    kcalPerMin: 6,
    defaultMinutes: 30,
    subExercises: ["벤치프레스", "인클라인 벤치프레스", "덤벨 플라이", "딥스", "푸시업", "디클라인 벤치프레스", "케이블 크로스오버"],
  },
  {
    label: "등운동",
    category: "strength",
    kcalPerMin: 6,
    defaultMinutes: 30,
    subExercises: ["랫풀다운", "티바로우", "데드리프트", "풀업", "시티드로우", "벤트오버 바벨로우", "원암 덤벨로우"],
  },
  {
    label: "팔운동",
    category: "strength",
    kcalPerMin: 5,
    defaultMinutes: 20,
    subExercises: ["바벨컬", "덤벨컬", "트라이셉스 익스텐션", "케이블 푸시다운", "해머컬", "스컬크러셔", "컨센트레이션컬"],
  },
  {
    label: "어깨운동",
    category: "strength",
    kcalPerMin: 5,
    defaultMinutes: 20,
    subExercises: ["숄더프레스", "사이드 레터럴 레이즈", "프론트 레이즈", "페이스풀", "아놀드프레스", "업라이트로우", "리버스 펙덱 플라이"],
  },
  {
    label: "하체운동",
    category: "strength",
    kcalPerMin: 7,
    defaultMinutes: 30,
    subExercises: ["스쿼트", "레그프레스", "런지", "레그컬", "카프레이즈", "레그익스텐션", "힙쓰러스트"],
  },
  {
    label: "코어운동",
    category: "strength",
    kcalPerMin: 5,
    defaultMinutes: 15,
    subExercises: ["플랭크", "크런치", "레그레이즈", "러시안트위스트", "사이드플랭크", "마운틴클라이머", "행잉레그레이즈"],
  },
  { label: "자전거", category: "cardio", kcalPerMin: 7, defaultMinutes: 30 },
  { label: "계단 오르기", category: "cardio", kcalPerMin: 10, defaultMinutes: 20 },
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

type BlockColor = { border: string; borderSoft: string; bg: string; text: string };

// 세 섹션(데일리체크/식단/운동)을 한눈에 구분할 수 있도록 각자 고유 색을 준다.
const DAILY_COLOR: BlockColor = { border: "border-zinc-500", borderSoft: "border-zinc-600/40", bg: "bg-zinc-500", text: "text-zinc-400" };
const DIET_COLOR: BlockColor = { border: "border-yellow-500", borderSoft: "border-yellow-500/40", bg: "bg-yellow-500", text: "text-yellow-400" };
const WORKOUT_COLOR: BlockColor = { border: "border-blue-500", borderSoft: "border-blue-500/40", bg: "bg-blue-500", text: "text-blue-400" };
const CALORIE_COLOR: BlockColor = { border: "border-emerald-500", borderSoft: "border-emerald-500/40", bg: "bg-emerald-500", text: "text-emerald-400" };
const OVER_BUDGET_COLOR: BlockColor = { border: "border-red-500", borderSoft: "border-red-500/40", bg: "bg-red-500", text: "text-red-400" };
const AI_COLOR: BlockColor = { border: "border-violet-500", borderSoft: "border-violet-500/40", bg: "bg-violet-500", text: "text-violet-400" };

// 하루 섭취 가능 칼로리 상한. 식단 섹션에서 계산되는 총 섭취 칼로리와 비교해 잔여 칼로리를 보여준다.
const DAILY_CALORIE_BUDGET = 1200;

// 다크/라이트 두 테마 모두에서 "가장 눈에 띄는 강조색"이 되도록 테마에 따라 반전되는 색.
// (다크: 흰 배경 + 검정 글씨, 라이트: 검정 배경 + 흰 글씨) — globals.css의 --pop-bg/--pop-fg 참고.
const DAY_BADGE_ACTIVE_CLASS = "border-[var(--pop-bg)] bg-[var(--pop-bg)] text-[var(--pop-fg)]";

type FoodItem =
  | { label: string; mode: "gram"; kcalPer100g: number }
  | { label: string; mode: "piece"; unit: string; kcalPerPiece: number };

const GRAM_STEPS = Array.from({ length: 100 }, (_, i) => (i + 1) * 10);

// 카탈로그 밖에서 이름+g또는개수(선택)+총칼로리로 직접 기록하는 항목. 단백질/탄수화물/지방/보충음식
// 중 하나로 분류하거나(그 매크로의 kcal에 합산되고 해당 섹션에 표시됨), 미분류(일반식)로 남길 수 있다.
// 100g당kcal은 총칼로리로부터 역산한 값(그램 단위일 때만 계산 가능)이며, 문자열로 인코딩해
// body_record.general_food_items(list[str]) 컬럼에 카테고리 상관없이 전부 저장한다.
type FoodCategory = "general" | "protein" | "carb" | "fat" | "supplement";

type CustomFoodEntry = {
  name: string;
  unit: "g" | "count";
  quantity: number | null;
  totalCalorie: number;
  kcalPer100g: number | null;
  category: FoodCategory;
};

const CUSTOM_FOOD_PREFIX = "CUSTOM|";

const FOOD_CATEGORY_OPTIONS: { value: FoodCategory; label: string }[] = [
  { value: "general", label: "일반식" },
  { value: "protein", label: "단백질" },
  { value: "carb", label: "탄수화물" },
  { value: "fat", label: "지방" },
  { value: "supplement", label: "보충음식" },
];

function caloriesPer100g(unit: "g" | "count", quantity: number | null, totalCalorie: number | null) {
  if (unit !== "g" || quantity === null || quantity <= 0) return null;
  if (totalCalorie === null || Number.isNaN(totalCalorie)) return null;
  return Math.round(((totalCalorie / quantity) * 100) * 10) / 10;
}

function encodeCustomFoodItem(entry: CustomFoodEntry) {
  return [
    CUSTOM_FOOD_PREFIX.slice(0, -1),
    entry.name.replaceAll("|", ""),
    entry.quantity ?? "",
    entry.unit,
    entry.totalCalorie,
    entry.category,
  ].join("|");
}

function decodeCustomFoodItem(raw: string): CustomFoodEntry | null {
  const parts = raw.split("|");
  if (parts.length !== 5 && parts.length !== 6) return null;
  const [, name, quantityRaw, unitRaw, totalCalorieRaw, categoryRaw] = parts;
  const unit: "g" | "count" = unitRaw === "count" ? "count" : "g";
  const quantity = quantityRaw === "" ? null : Number(quantityRaw);
  const totalCalorie = Number(totalCalorieRaw);
  // 5-part(레거시) 항목은 카테고리가 없었으므로 일반식으로 취급한다.
  const category: FoodCategory = FOOD_CATEGORY_OPTIONS.some((o) => o.value === categoryRaw)
    ? (categoryRaw as FoodCategory)
    : "general";
  if (!name || Number.isNaN(totalCalorie)) return null;
  return {
    name,
    unit,
    quantity: quantity === null || Number.isNaN(quantity) ? null : quantity,
    totalCalorie,
    kcalPer100g: caloriesPer100g(unit, quantity ?? null, totalCalorie),
    category,
  };
}

const PROTEIN_FOODS: FoodItem[] = [
  { label: "달걀", mode: "piece", unit: "1개", kcalPerPiece: 100 },
  { label: "참치 마일드", mode: "gram", kcalPer100g: 126 },
  { label: "닭가슴살", mode: "gram", kcalPer100g: 100 },
  { label: "닭가슴살스팸", mode: "gram", kcalPer100g: 170 },
];

const CARB_FOODS: FoodItem[] = [
  { label: "햇반", mode: "gram", kcalPer100g: 150 },
  { label: "생고구마", mode: "gram", kcalPer100g: 120 },
  { label: "감자", mode: "gram", kcalPer100g: 80 },
];

const FAT_FOODS: FoodItem[] = [
  { label: "아보카도", mode: "gram", kcalPer100g: 160 },
  { label: "브로콜리", mode: "gram", kcalPer100g: 30 },
];

const SUPPLEMENT_FOODS: { label: string; unit: string }[] = [
  { label: "블루베리", unit: "30g" },
  { label: "방울토마토", unit: "30g" },
  { label: "올리브오일", unit: "한스푼" },
];

const WATER_PRESETS = [0, 0.3, 0.5, 0.8, 1.0, 1.3, 1.5, 1.8, 2.0, 2.3, 2.5, 3.0];

const SLEEP_HOURS = Array.from({ length: 25 }, (_, i) => i);

const MOOD_OPTIONS = [
  { score: 1, icon: "🤨" },
  { score: 2, icon: "🙃" },
  { score: 3, icon: "🤔" },
  { score: 4, icon: "🤓" },
  { score: 5, icon: "😎" },
];

const READY_LEVELS = [
  {
    min: 80,
    label: "AWESOME",
    icon: "🔵",
    text: "컨디션 최상이에요! 오늘같은 날이 자주 있으면 좋겠네요.",
    bg: "bg-blue-600",
  },
  {
    min: 50,
    label: "GOOD",
    icon: "🟢",
    text: "좋은 상태예요. 지금 이 페이스, 딱 좋아요.",
    bg: "bg-emerald-600",
  },
  {
    min: 30,
    label: "SOSO",
    icon: "🟡",
    text: "무난해요. 크게 무리 없이 하루를 챙기고 있어요.",
    bg: "bg-yellow-500",
  },
  {
    min: 10,
    label: "CARE",
    icon: "🟠",
    text: "몸이 살짝 신호를 보내고 있어요. 오늘은 무리하지 말아요.",
    bg: "bg-orange-600",
  },
  {
    min: 0,
    label: "RECOVERY",
    icon: "🔴",
    text: "지금은 회복이 먼저예요. 잘 쉬는 것도 관리의 일부니까요.",
    bg: "bg-red-600",
  },
];

const BLACK_LEVEL = {
  min: -1,
  label: "BREAK",
  icon: "⚫",
  text: "아직 아무것도 체크 안 했어요. 하나만 눌러도 오늘이 시작돼요.",
  bg: "bg-black border-2 border-zinc-700",
};

const SICK_LEVEL = {
  min: -1,
  label: "SICK DAY",
  icon: "🤒",
  text: "오늘은 아픈 날이에요. 무리하지 말고 푹 쉬는 게 우선이에요.",
  bg: "bg-violet-600",
};

const DEFAULT_PROTEIN_TARGET = 430;
const DEFAULT_CARB_TARGET = 700;
const DEFAULT_FAT_TARGET = 160;
const DEFAULT_WATER_TARGET = 2.0;
const SLEEP_TARGET = 7;

type SelectedWorkout = {
  minutes: number;
  details: Set<string>;
};

// 카탈로그(WORKOUT_TYPES)에 없는 유산소 운동을 이름+분+소모칼로리로 직접 기록하는 항목.
// workout_item 테이블은 workout_type이 자유 문자열이라 별도 인코딩 없이 그대로 workout_items에 실어 보낸다.
type CustomWorkoutEntry = {
  name: string;
  minutes: number;
  calorieEstimate: number;
};

type PeriodStats = {
  days_logged: number;
  avg_weight_kg: number | null;
  avg_sleep_hours: number | null;
  avg_water_liter: number | null;
  avg_protein_kcal: number | null;
  avg_carb_kcal: number | null;
  avg_fat_kcal: number | null;
  avg_mood_score: number | null;
  workout_days: number;
  full_medication_days: number;
  binge_days: number;
  period_days: number;
};

type HistoryRow = {
  record_date: string;
  weight_kg: number | null;
  sleep_hours: number | null;
  water_liter: number | null;
  protein_kcal: number | null;
  carb_kcal: number | null;
  fat_kcal: number | null;
  workout_done_yn: boolean | null;
  mood_score: number | null;
  binge_yn: boolean | null;
};

type NumericHistoryKey = "weight_kg" | "sleep_hours" | "water_liter" | "protein_kcal" | "carb_kcal" | "fat_kcal";

const TREND_METRICS: { key: NumericHistoryKey; title: string; unit: string }[] = [
  { key: "weight_kg", title: "⚖️ 체중", unit: "kg" },
  { key: "sleep_hours", title: "😴 수면", unit: "h" },
  { key: "water_liter", title: "💧 수분", unit: "L" },
  { key: "protein_kcal", title: "🥩 단백질", unit: "kcal" },
  { key: "carb_kcal", title: "🍚 탄수화물", unit: "kcal" },
  { key: "fat_kcal", title: "🥑 지방", unit: "kcal" },
];

function today() {
  const now = new Date();
  const offset = now.getTimezoneOffset() * 60000;
  return new Date(now.getTime() - offset).toISOString().slice(0, 10);
}

function kcalFor(type: string, minutes: number) {
  const entry = WORKOUT_TYPES.find((w) => w.label === type);
  return Math.round((entry?.kcalPerMin ?? 6) * minutes);
}

function workoutCategoryTotals(
  category: "strength" | "cardio",
  selectedWorkouts: Map<string, SelectedWorkout>,
  customWorkouts: CustomWorkoutEntry[] = []
) {
  const catalogTotals = WORKOUT_TYPES.filter((w) => w.category === category).reduce(
    (totals, w) => {
      const selected = selectedWorkouts.get(w.label);
      if (!selected) return totals;
      return {
        minutes: totals.minutes + selected.minutes,
        kcal: totals.kcal + kcalFor(w.label, selected.minutes),
      };
    },
    { minutes: 0, kcal: 0 }
  );

  return customWorkouts.reduce(
    (totals, w) => ({ minutes: totals.minutes + w.minutes, kcal: totals.kcal + w.calorieEstimate }),
    catalogTotals
  );
}

function foodKcal(food: FoodItem, amount: number) {
  return food.mode === "gram" ? Math.round((amount / 100) * food.kcalPer100g) : amount * food.kcalPerPiece;
}

function computeKcal(foods: FoodItem[], counts: Map<string, number>) {
  return foods.reduce((sum, food) => sum + foodKcal(food, counts.get(food.label) ?? 0), 0);
}

function buildFoodItems(foods: FoodItem[], counts: Map<string, number>): string[] {
  return foods
    .filter((food) => (counts.get(food.label) ?? 0) > 0)
    .map((food) => `${food.label} ${counts.get(food.label)}${food.mode === "gram" ? "g" : "개"}`);
}

function parseFoodItems(items: string[]) {
  const map = new Map<string, number>();
  items.forEach((item) => {
    const match = item.match(/^(.*) (\d+)(?:g|개)$/);
    if (match) map.set(match[1], parseInt(match[2], 10));
  });
  return map;
}

function parseGeneralFoodItems(items: string[]): CustomFoodEntry[] {
  return items.map(decodeCustomFoodItem).filter((item): item is CustomFoodEntry => item !== null);
}

function sumCustomKcal(items: CustomFoodEntry[], category: FoodCategory) {
  return items.filter((item) => item.category === category).reduce((sum, item) => sum + item.totalCalorie, 0);
}

// 특정 카테고리에 속한 항목만, 원본 배열에서의 index와 함께 뽑아낸다 (수정/삭제 시 원본 index가 필요).
function customEntriesByCategory(items: CustomFoodEntry[], category: FoodCategory) {
  return items
    .map((item, index) => ({ item, index }))
    .filter((entry) => entry.item.category === category);
}

// 이름이 같은 항목이 여러 날짜에 걸쳐 반복될 수 있으므로, 가장 최근 값(먼저 나오는 항목)만 남긴다.
function dedupeFoodHistoryByName(items: CustomFoodEntry[]): CustomFoodEntry[] {
  const seen = new Set<string>();
  const deduped: CustomFoodEntry[] = [];
  items.forEach((item) => {
    if (seen.has(item.name)) return;
    seen.add(item.name);
    deduped.push(item);
  });
  return deduped;
}

function round1(value: number | null) {
  return value === null || value === undefined ? "-" : Math.round(value * 10) / 10;
}

function computeReady({
  sleepHours,
  waterLiter,
  waterTarget,
  proteinKcal,
  proteinTarget,
  workoutDone,
  morningMed,
  eveningMed,
}: {
  sleepHours: number;
  waterLiter: number;
  waterTarget: number;
  proteinKcal: number;
  proteinTarget: number;
  workoutDone: boolean;
  morningMed: boolean;
  eveningMed: boolean;
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

  if (proteinKcal >= proteinTarget) score += 15;
  else if (proteinKcal >= proteinTarget * 0.75) score += 10;
  else if (proteinKcal >= proteinTarget * 0.5) score += 5;

  score += workoutDone ? 20 : 10;

  if (morningMed && eveningMed) score += 15;
  else if (morningMed || eveningMed) score += 8;

  const level = READY_LEVELS.find((l) => score >= l.min) ?? READY_LEVELS[READY_LEVELS.length - 1];

  return { score, level };
}

function snapshotFormState(state: {
  morningMed: boolean;
  eveningMed: boolean;
  weightKg: number | null;
  waterLiter: number;
  sleepHours: number;
  binge: boolean;
  isSick: boolean;
  moodScore: number | null;
  workoutComment: string;
  selectedWorkouts: Map<string, SelectedWorkout>;
  customCardioWorkouts: CustomWorkoutEntry[];
  proteinCounts: Map<string, number>;
  carbCounts: Map<string, number>;
  fatCounts: Map<string, number>;
  customMealItems: CustomFoodEntry[];
  supplementItems: Set<string>;
}) {
  return JSON.stringify({
    morningMed: state.morningMed,
    eveningMed: state.eveningMed,
    weightKg: state.weightKg,
    waterLiter: state.waterLiter,
    sleepHours: state.sleepHours,
    binge: state.binge,
    isSick: state.isSick,
    moodScore: state.moodScore,
    workoutComment: state.workoutComment,
    workouts: Array.from(state.selectedWorkouts.entries())
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([type, w]) => [type, w.minutes, Array.from(w.details).sort()]),
    customCardio: state.customCardioWorkouts.map((w) => [w.name, w.minutes, w.calorieEstimate]),
    protein: Array.from(state.proteinCounts.entries())
      .filter(([, count]) => count > 0)
      .sort(([a], [b]) => a.localeCompare(b)),
    carb: Array.from(state.carbCounts.entries())
      .filter(([, count]) => count > 0)
      .sort(([a], [b]) => a.localeCompare(b)),
    fat: Array.from(state.fatCounts.entries())
      .filter(([, count]) => count > 0)
      .sort(([a], [b]) => a.localeCompare(b)),
    generalFood: state.customMealItems.map(encodeCustomFoodItem),
    supplement: Array.from(state.supplementItems).sort(),
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
  const loadedDateRef = useRef<string | null>(null);
  const autoSaveTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  // pollCoachFeedback의 재귀 setTimeout 체인을 무효화하기 위한 세대 번호.
  // 날짜가 바뀌거나 새 코칭 요청이 시작되면 증가시켜, 이전 체인이 더 이상
  // fetch/setState를 하지 않고 스스로 멈추게 한다.
  const coachPollGenRef = useRef(0);

  // 테마: 기본은 검은색(dark), localStorage에 저장해 다음 방문에도 유지한다.
  const [theme, setTheme] = useState<"dark" | "light">("dark");

  useEffect(() => {
    const saved = localStorage.getItem("gk21-theme");
    if (saved === "light" || saved === "dark") setTheme(saved);
  }, []);

  useEffect(() => {
    localStorage.setItem("gk21-theme", theme);
  }, [theme]);

  const [recordDate, setRecordDate] = useState(today());
  const [dataReady, setDataReady] = useState(false);
  const [morningMed, setMorningMed] = useState(false);
  const [eveningMed, setEveningMed] = useState(false);
  const [selectedWorkouts, setSelectedWorkouts] = useState<Map<string, SelectedWorkout>>(new Map());
  const [customCardioWorkouts, setCustomCardioWorkouts] = useState<CustomWorkoutEntry[]>([]);
  const [workoutComment, setWorkoutComment] = useState("");
  const [proteinCounts, setProteinCounts] = useState<Map<string, number>>(new Map());
  const [proteinTarget, setProteinTarget] = useState(DEFAULT_PROTEIN_TARGET);
  const [carbCounts, setCarbCounts] = useState<Map<string, number>>(new Map());
  const [carbTarget, setCarbTarget] = useState(DEFAULT_CARB_TARGET);
  const [fatCounts, setFatCounts] = useState<Map<string, number>>(new Map());
  const [fatTarget, setFatTarget] = useState(DEFAULT_FAT_TARGET);
  const [supplementItems, setSupplementItems] = useState<Set<string>>(new Set());
  const [customMealItems, setCustomMealItems] = useState<CustomFoodEntry[]>([]);
  const [foodHistory, setFoodHistory] = useState<CustomFoodEntry[]>([]);
  const [foodHistoryQuery, setFoodHistoryQuery] = useState("");
  const [weightKg, setWeightKg] = useState<number | null>(null);
  const [weightTarget, setWeightTarget] = useState<number | null>(null);
  const [waterLiter, setWaterLiter] = useState(0);
  const [waterTarget, setWaterTarget] = useState(DEFAULT_WATER_TARGET);
  const [sleepHours, setSleepHours] = useState(0);
  const [binge, setBinge] = useState(false);
  const [isSick, setIsSick] = useState(false);
  const [moodScore, setMoodScore] = useState<number | null>(null);

  const [autoSaveStatus, setAutoSaveStatus] = useState<"idle" | "saving" | "saved">("idle");
  const [coachStatus, setCoachStatus] = useState<"idle" | "loading" | "ready">("idle");
  const [coachText, setCoachText] = useState("");
  const [coachWorkoutText, setCoachWorkoutText] = useState("");
  const [coachMealText, setCoachMealText] = useState("");

  const [view, setView] = useState<"today" | "week" | "month">("today");
  const [stats, setStats] = useState<PeriodStats | null>(null);
  const [history, setHistory] = useState<HistoryRow[] | null>(null);
  const [statsLoading, setStatsLoading] = useState(false);

  const proteinKcal = useMemo(
    () => computeKcal(PROTEIN_FOODS, proteinCounts) + sumCustomKcal(customMealItems, "protein"),
    [proteinCounts, customMealItems]
  );
  const carbKcal = useMemo(
    () => computeKcal(CARB_FOODS, carbCounts) + sumCustomKcal(customMealItems, "carb"),
    [carbCounts, customMealItems]
  );
  const fatKcal = useMemo(
    () => computeKcal(FAT_FOODS, fatCounts) + sumCustomKcal(customMealItems, "fat"),
    [fatCounts, customMealItems]
  );
  const generalFoodKcal = useMemo(() => sumCustomKcal(customMealItems, "general"), [customMealItems]);
  const supplementCustomKcal = useMemo(() => sumCustomKcal(customMealItems, "supplement"), [customMealItems]);
  const totalDietKcal = proteinKcal + carbKcal + fatKcal + generalFoodKcal + supplementCustomKcal;
  const remainingKcal = DAILY_CALORIE_BUDGET - totalDietKcal;
  const filteredFoodHistory = useMemo(() => {
    const query = foodHistoryQuery.trim();
    if (!query) return foodHistory;
    return foodHistory.filter((item) => item.name.includes(query));
  }, [foodHistory, foodHistoryQuery]);

  const workoutDone = selectedWorkouts.size > 0 || customCardioWorkouts.length > 0;
  // 근력/유산소 분류별 합계를 한 번만 계산해서 Section 부제목과 운동 섹션 렌더링에서 같이 쓴다
  // (예전엔 같은 값을 useMemo 밖에서 JSX 중에 한 번 더 계산했음).
  const workoutBreakdown = useMemo(
    () => ({
      strength: workoutCategoryTotals("strength", selectedWorkouts),
      cardio: workoutCategoryTotals("cardio", selectedWorkouts, customCardioWorkouts),
    }),
    [selectedWorkouts, customCardioWorkouts]
  );
  const totalWorkoutKcal = workoutBreakdown.strength.kcal + workoutBreakdown.cardio.kcal;
  const todaySchedule = useMemo(() => scheduleFor(recordDate), [recordDate]);

  // DB에 기록 행이 존재하는지가 아니라, 실제로 뭔가 하나라도 체크했는지로 BREAK 여부를 판단한다.
  const hasAnyInput = useMemo(() => {
    const hasProtein = Array.from(proteinCounts.values()).some((count) => count > 0);
    const hasCarb = Array.from(carbCounts.values()).some((count) => count > 0);
    const hasFat = Array.from(fatCounts.values()).some((count) => count > 0);
    return (
      morningMed ||
      eveningMed ||
      selectedWorkouts.size > 0 ||
      customCardioWorkouts.length > 0 ||
      hasProtein ||
      hasCarb ||
      hasFat ||
      customMealItems.length > 0 ||
      supplementItems.size > 0 ||
      weightKg !== null ||
      waterLiter > 0 ||
      sleepHours > 0 ||
      binge ||
      moodScore !== null ||
      isSick
    );
  }, [
    morningMed,
    eveningMed,
    selectedWorkouts,
    customCardioWorkouts,
    proteinCounts,
    carbCounts,
    fatCounts,
    customMealItems,
    supplementItems,
    weightKg,
    waterLiter,
    sleepHours,
    binge,
    moodScore,
    isSick,
  ]);

  const ready = useMemo(() => {
    if (isSick) return { score: 0, level: SICK_LEVEL };
    if (!hasAnyInput) return { score: 0, level: BLACK_LEVEL };

    return computeReady({
      sleepHours,
      waterLiter,
      waterTarget,
      proteinKcal,
      proteinTarget,
      workoutDone,
      morningMed,
      eveningMed,
    });
  }, [
    hasAnyInput,
    isSick,
    sleepHours,
    waterLiter,
    waterTarget,
    proteinKcal,
    proteinTarget,
    workoutDone,
    morningMed,
    eveningMed,
  ]);

  // 목표치 달성이 아니라 "하나라도 체크/기록했는지"를 기준으로 성공 여부를 판단한다.
  const dietGood = totalDietKcal > 0;

  const dayBadges = [
    { key: "workout", icon: "🏋", label: "운동", good: workoutDone, activeClass: DAY_BADGE_ACTIVE_CLASS },
    { key: "diet", icon: "🍱", label: "식단", good: dietGood, activeClass: DAY_BADGE_ACTIVE_CLASS },
    { key: "water", icon: "💧", label: "물", good: waterLiter > 0, activeClass: DAY_BADGE_ACTIVE_CLASS },
    { key: "sleep", icon: "😴", label: "수면", good: sleepHours > 0, activeClass: DAY_BADGE_ACTIVE_CLASS },
    { key: "med", icon: "💊", label: "복약", good: morningMed || eveningMed, activeClass: DAY_BADGE_ACTIVE_CLASS },
  ];

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

  function addCustomCardioWorkout(entry: CustomWorkoutEntry) {
    setCustomCardioWorkouts((prev) => [...prev, entry]);
  }

  function updateCustomCardioWorkout(index: number, entry: CustomWorkoutEntry) {
    setCustomCardioWorkouts((prev) => prev.map((item, i) => (i === index ? entry : item)));
  }

  function removeCustomCardioWorkout(index: number) {
    setCustomCardioWorkouts((prev) => prev.filter((_, i) => i !== index));
  }

  // useCallback + 함수형 setState(prev => ...)로만 구현해 항상 같은 함수 아이덴티티를 유지한다.
  // FoodSection을 memo로 감쌌기 때문에, 이렇게 안정된 콜백을 넘겨야 무관한 필드를
  // 수정할 때(예: 몸무게, 운동 코멘트) 단백질/탄수화물/지방 섹션이 불필요하게 리렌더링되지 않는다.
  const updateFoodCount = useCallback(
    (
      setCounts: React.Dispatch<React.SetStateAction<Map<string, number>>>,
      label: string,
      count: number
    ) => {
      setCounts((prev) => {
        const next = new Map(prev);
        next.set(label, Math.max(0, count));
        return next;
      });
    },
    []
  );

  const onChangeProteinCount = useCallback(
    (label: string, v: number) => updateFoodCount(setProteinCounts, label, v),
    [updateFoodCount]
  );
  const onChangeCarbCount = useCallback(
    (label: string, v: number) => updateFoodCount(setCarbCounts, label, v),
    [updateFoodCount]
  );
  const onChangeFatCount = useCallback(
    (label: string, v: number) => updateFoodCount(setFatCounts, label, v),
    [updateFoodCount]
  );

  function toggleSupplement(label: string) {
    setSupplementItems((prev) => {
      const next = new Set(prev);
      if (next.has(label)) next.delete(label);
      else next.add(label);
      return next;
    });
  }

  function addCustomMealItem(entry: CustomFoodEntry) {
    setCustomMealItems((prev) => [...prev, entry]);
  }

  const updateCustomMealItem = useCallback((index: number, entry: CustomFoodEntry) => {
    setCustomMealItems((prev) => prev.map((item, i) => (i === index ? entry : item)));
  }, []);

  const removeCustomMealItem = useCallback((index: number) => {
    setCustomMealItems((prev) => prev.filter((_, i) => i !== index));
  }, []);

  function buildPayload(triggerAiCoaching: boolean) {
    const bikeMinutes = selectedWorkouts.get("자전거")?.minutes ?? 0;

    const completedWorkout = [
      ...Array.from(selectedWorkouts.entries()).map(([type, w]) => {
        const detailText = w.details.size > 0 ? ` (${Array.from(w.details).join(", ")})` : "";
        return `${type} ${w.minutes}분${detailText}`;
      }),
      ...customCardioWorkouts.map((w) => `${w.name} ${w.minutes}분`),
    ].join(", ");

    const proteinItems = buildFoodItems(PROTEIN_FOODS, proteinCounts);
    const carbItems = buildFoodItems(CARB_FOODS, carbCounts);
    const fatItems = buildFoodItems(FAT_FOODS, fatCounts);
    const generalFoodItems = customMealItems.map(encodeCustomFoodItem);

    return {
      record_date: recordDate,
      // 자동저장에서는 AI 코칭을 트리거하지 않는다 — "AI 코칭 받기"를 눌렀을 때만 true.
      // (그전에는 필드 하나 바꿀 때마다 자동저장이 실제 OpenAI 호출을 매번 발생시켰음)
      trigger_ai_coaching: triggerAiCoaching,
      score: ready.score,
      grade: ready.level.label,
      mood_score: moodScore,
      memo: workoutDone ? workoutComment || null : null,
      is_sick: isSick,
      morning_med_taken: morningMed,
      evening_med_taken: eveningMed,
      medication_note: buildMedicationNote(morningMed, eveningMed),
      body: {
        weight_kg: weightKg,
        water_liter: waterLiter,
        protein_kcal: proteinKcal,
        protein_items: proteinItems,
        carb_kcal: carbKcal,
        carb_items: carbItems,
        fat_kcal: fatKcal,
        fat_items: fatItems,
        supplement_items: Array.from(supplementItems),
        general_food_items: generalFoodItems,
        binge_yn: binge,
      },
      workout: {
        planned_workout: workoutDone ? completedWorkout : null,
        completed_workout: workoutDone ? completedWorkout : null,
        bike_minutes: bikeMinutes,
        workout_done_yn: workoutDone,
      },
      workout_items: [
        ...Array.from(selectedWorkouts.entries()).map(([type, w]) => ({
          workout_type: type,
          minutes: w.minutes,
          calorie_estimate: kcalFor(type, w.minutes),
          detail: w.details.size > 0 ? Array.from(w.details).join(", ") : null,
        })),
        ...customCardioWorkouts.map((w) => ({
          workout_type: w.name,
          minutes: w.minutes,
          calorie_estimate: w.calorieEstimate,
          detail: null,
        })),
      ],
      meal: null,
      sleep: {
        sleep_hours: sleepHours,
        sleep_quality_score: sleepHours >= 7 ? 85 : 70,
        wake_condition: ready.level.label,
      },
    };
  }

  async function saveToServer(triggerAiCoaching: boolean) {
    const res = await fetch("/api/day", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(buildPayload(triggerAiCoaching)),
    });
    const data = await res.json();
    if (!res.ok || !data.success) throw new Error(JSON.stringify(data));
    return data;
  }

  async function pollCoachFeedback(date: string, attemptsLeft: number, generation: number) {
    // 폴링 도중 날짜가 바뀌거나 새 코칭 요청이 시작되면 이 체인은 더 이상 유효하지 않다.
    if (generation !== coachPollGenRef.current) return;

    try {
      const res = await fetch(`/api/dashboard?record_date=${date}`, { cache: "no-store" });
      const data = await res.json();

      if (generation !== coachPollGenRef.current) return;

      const ai = data?.ai;
      const text = ai?.cards?.coach ?? ai?.summary;

      if (text) setCoachText(text);
      if (ai?.comments?.workout) setCoachWorkoutText(ai.comments.workout);
      if (ai?.comments?.meal) setCoachMealText(ai.comments.meal);

      if (ai?.overview?.status === "COMPLETED" || attemptsLeft <= 0) {
        setCoachStatus("ready");
        return;
      }

      setTimeout(() => pollCoachFeedback(date, attemptsLeft - 1, generation), 3000);
    } catch {
      if (generation === coachPollGenRef.current) setCoachStatus("ready");
    }
  }

  // 일반식 직접입력 히스토리는 날짜와 무관하게 한 번만 불러온다 (조회해서 선택하기용).
  useEffect(() => {
    let cancelled = false;

    fetch("/api/food-history", { cache: "no-store" })
      .then((res) => res.json())
      .then((data) => {
        if (cancelled) return;
        const decoded = parseGeneralFoodItems(data?.items ?? []);
        setFoodHistory(dedupeFoodHistoryByName(decoded));
      })
      .catch(() => {
        if (!cancelled) setFoodHistory([]);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  // 날짜가 바뀌면 그 날짜의 기존 기록을 불러와서 폼을 채운다 (없으면 기본값으로 초기화).
  useEffect(() => {
    let cancelled = false;
    setDataReady(false);
    setCoachStatus("idle");
    setCoachText("");
    setCoachWorkoutText("");
    setCoachMealText("");
    setAutoSaveStatus("idle");
    // 날짜를 바꾸면 이전 날짜에 대해 돌고 있던 AI 코칭 폴링 체인을 무효화한다.
    coachPollGenRef.current += 1;

    fetch(`/api/dashboard?record_date=${recordDate}`, { cache: "no-store" })
      .then((res) => res.json())
      .then((data) => {
        if (cancelled) return;

        const d = data?.dashboard;
        const detail = data?.detail;

        const loaded = {
          morningMed: d?.morning_med_taken ?? false,
          eveningMed: d?.evening_med_taken ?? false,
          weightKg: d?.weight_kg ?? null,
          waterLiter: d?.water_liter ?? 0,
          sleepHours: d?.sleep_hours ?? 0,
          binge: d?.binge_yn ?? false,
          isSick: detail?.is_sick ?? false,
          moodScore: d?.mood_score ?? null,
          workoutComment: d?.memo ?? "",
        };

        const workoutMap = new Map<string, SelectedWorkout>();
        const customCardioList: CustomWorkoutEntry[] = [];
        (detail?.workout_items ?? []).forEach(
          (item: { workout_type: string; minutes: number; calorie_estimate: number | null; detail: string | null }) => {
            const isKnownType = WORKOUT_TYPES.some((w) => w.label === item.workout_type);
            if (isKnownType) {
              workoutMap.set(item.workout_type, {
                minutes: item.minutes,
                details: new Set(item.detail ? item.detail.split(", ") : []),
              });
            } else {
              customCardioList.push({
                name: item.workout_type,
                minutes: item.minutes,
                calorieEstimate: item.calorie_estimate ?? 0,
              });
            }
          }
        );

        const proteinMap = parseFoodItems(detail?.protein_items ?? []);
        const carbMap = parseFoodItems(detail?.carb_items ?? []);
        const fatMap = parseFoodItems(detail?.fat_items ?? []);
        const generalFoodList = parseGeneralFoodItems(detail?.general_food_items ?? []);
        const supplementSet = new Set<string>(detail?.supplement_items ?? []);

        // 자동저장 effect가 "방금 불러온 값 그대로"인 경우 저장을 건너뛸 수 있도록 스냅샷을 먼저 기록해둔다.
        lastLoadedSnapshotRef.current = snapshotFormState({
          ...loaded,
          selectedWorkouts: workoutMap,
          customCardioWorkouts: customCardioList,
          proteinCounts: proteinMap,
          carbCounts: carbMap,
          fatCounts: fatMap,
          customMealItems: generalFoodList,
          supplementItems: supplementSet,
        });

        setMorningMed(loaded.morningMed);
        setEveningMed(loaded.eveningMed);
        setWeightKg(loaded.weightKg);
        setWaterLiter(loaded.waterLiter);
        setSleepHours(loaded.sleepHours);
        setBinge(loaded.binge);
        setIsSick(loaded.isSick);
        setMoodScore(loaded.moodScore);
        setWorkoutComment(loaded.workoutComment);
        setSelectedWorkouts(workoutMap);
        setCustomCardioWorkouts(customCardioList);
        setProteinCounts(proteinMap);
        setCarbCounts(carbMap);
        setFatCounts(fatMap);
        setCustomMealItems(generalFoodList);
        setSupplementItems(supplementSet);

        if (data?.goal?.target_protein_kcal) {
          setProteinTarget(data.goal.target_protein_kcal);
        }
        if (data?.goal?.target_carb_kcal) {
          setCarbTarget(data.goal.target_carb_kcal);
        }
        if (data?.goal?.target_fat_kcal) {
          setFatTarget(data.goal.target_fat_kcal);
        }
        if (data?.goal?.target_water_liter) {
          setWaterTarget(data.goal.target_water_liter);
        }
        if (data?.goal?.target_weight_kg) {
          setWeightTarget(data.goal.target_weight_kg);
        }

        loadedDateRef.current = recordDate;
        setDataReady(true);
      });

    return () => {
      cancelled = true;
    };
  }, [recordDate]);

  // 자동 저장: 방금 불러온 값과 달라졌을 때만 2초 후 조용히 저장한다.
  // loadedDateRef가 현재 날짜와 아직 일치하지 않으면(로딩 완료 전) 절대 저장을 트리거하지 않는다.
  useEffect(() => {
    if (loadedDateRef.current !== recordDate) return;

    const currentSnapshot = snapshotFormState({
      morningMed,
      eveningMed,
      weightKg,
      waterLiter,
      sleepHours,
      binge,
      isSick,
      moodScore,
      workoutComment,
      selectedWorkouts,
      customCardioWorkouts,
      proteinCounts,
      carbCounts,
      fatCounts,
      customMealItems,
      supplementItems,
    });

    if (currentSnapshot === lastLoadedSnapshotRef.current) return;

    if (autoSaveTimer.current) clearTimeout(autoSaveTimer.current);

    autoSaveTimer.current = setTimeout(async () => {
      setAutoSaveStatus("saving");
      try {
        await saveToServer(false);
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
    customCardioWorkouts,
    proteinCounts,
    carbCounts,
    fatCounts,
    customMealItems,
    supplementItems,
    weightKg,
    waterLiter,
    sleepHours,
    binge,
    isSick,
    moodScore,
    workoutComment,
  ]);

  async function requestCoaching() {
    setCoachStatus("loading");
    setCoachText("");
    setCoachWorkoutText("");
    setCoachMealText("");
    // 이전에 돌고 있던 폴링 체인(있다면)을 무효화하고 이번 요청만의 세대를 새로 만든다.
    const myGeneration = ++coachPollGenRef.current;
    if (autoSaveTimer.current) clearTimeout(autoSaveTimer.current);

    try {
      setAutoSaveStatus("saving");
      await saveToServer(true);
      lastLoadedSnapshotRef.current = snapshotFormState({
        morningMed,
        eveningMed,
        weightKg,
        waterLiter,
        sleepHours,
        binge,
        isSick,
        moodScore,
        workoutComment,
        selectedWorkouts,
        customCardioWorkouts,
        proteinCounts,
        carbCounts,
        fatCounts,
        customMealItems,
        supplementItems,
      });
      setAutoSaveStatus("saved");
      pollCoachFeedback(recordDate, 8, myGeneration);
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
    <main data-theme={theme} className="min-h-screen bg-zinc-950 pb-8 text-zinc-100 transition-colors duration-300">
      <div className="mx-auto max-w-xl p-4">
        <div className="flex items-center justify-between gap-2">
          <div className="flex min-w-0 items-baseline gap-2">
            <h1 className="shrink-0 text-2xl font-black">🧤 GK21</h1>
            <span className="truncate text-sm font-bold text-zinc-400">{todaySchedule.dayLabel}</span>
          </div>
          <div className="flex shrink-0 items-center gap-2">
            <button
              type="button"
              onClick={() => setTheme((t) => (t === "dark" ? "light" : "dark"))}
              className="grid h-9 w-9 shrink-0 place-items-center rounded-full border border-zinc-700 bg-zinc-900 text-base"
              aria-label={theme === "dark" ? "라이트 모드로 전환" : "다크 모드로 전환"}
            >
              {theme === "dark" ? "🌙" : "☀️"}
            </button>
            <input
              type="date"
              value={recordDate}
              onChange={(e) => setRecordDate(e.target.value)}
              className="rounded-full border border-zinc-700 bg-zinc-900 px-4 py-2 text-sm font-bold text-zinc-100"
            />
          </div>
        </div>

        <section
          className={[
            "mt-3 rounded-3xl p-6 shadow-lg transition-colors duration-300",
            !dataReady
              ? "border border-zinc-800 bg-zinc-900 text-zinc-100"
              : isSick || !hasAnyInput
                ? ["text-white", ready.level.bg].join(" ")
                : "border border-zinc-800 bg-zinc-900 text-zinc-100",
          ].join(" ")}
        >
          <p
            className={[
              "text-center text-sm font-black uppercase tracking-wide",
              dataReady && (isSick || !hasAnyInput) ? "text-white/70" : "text-zinc-500",
            ].join(" ")}
          >
            {recordDate === today() ? "오늘 기록" : `${recordDate} 기록`}
          </p>

          {!dataReady ? (
            <p className="mt-2 text-center text-lg font-bold text-zinc-500">불러오는 중...</p>
          ) : isSick || !hasAnyInput ? (
            <div className="text-center">
              <p className="mt-2 text-4xl font-black">
                {ready.level.icon} {ready.level.label}
              </p>
              <p className="mt-2 font-bold text-white/90">{ready.level.text}</p>
            </div>
          ) : (
            <div className="mt-3 flex flex-wrap justify-center gap-2">
              {dayBadges.map((b) => (
                <span
                  key={b.key}
                  className={[
                    "inline-flex items-center gap-1.5 rounded-full border-2 px-3.5 py-2 text-sm font-bold transition-colors",
                    b.good ? b.activeClass : "border-zinc-700 bg-zinc-800 text-zinc-400",
                  ].join(" ")}
                >
                  {b.good && "✓ "}
                  {b.icon} {b.label}
                </span>
              ))}
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
                view === tab.key ? DAY_BADGE_ACTIVE_CLASS : "border-zinc-800 bg-zinc-900 text-zinc-400",
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
                {TREND_METRICS.map((m) => (
                  <TrendChart
                    key={m.key}
                    title={m.title}
                    unit={m.unit}
                    data={history.map((h) => h[m.key])}
                    dates={history.map((h) => h.record_date)}
                  />
                ))}
                <WorkoutDots data={history.map((h) => h.workout_done_yn)} dates={history.map((h) => h.record_date)} />
              </>
            )}
          </section>
        ) : (
          <>
            <Section title="📋 데일리 체크" color={DAILY_COLOR} collapsible defaultOpen={false}>
              <div className="space-y-4">
                <CollapsibleBlock title="⚡ 빠른 체크">
                  <div className="flex gap-2 overflow-x-auto pb-1">
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
                </CollapsibleBlock>

                <CollapsibleBlock
                  title={`⚖️ 체중 · ${weightKg !== null ? `${weightKg}kg` : "-"}${weightTarget !== null ? ` / 목표 ${weightTarget}kg` : ""}`}
                >
                  <input
                    type="number"
                    inputMode="decimal"
                    step={0.1}
                    value={weightKg ?? ""}
                    onChange={(e) => setWeightKg(e.target.value === "" ? null : parseFloat(e.target.value))}
                    placeholder="체중 입력 (kg)"
                    className="w-full rounded-2xl border border-zinc-700 bg-zinc-800 p-3 text-lg font-black text-zinc-100 placeholder:text-zinc-500 placeholder:font-normal"
                  />
                </CollapsibleBlock>

                <CollapsibleBlock title={`💧 물 · ${waterLiter.toFixed(1)}L / 목표 ${waterTarget.toFixed(1)}L`}>
                  <ScaleRow
                    values={WATER_PRESETS}
                    active={waterLiter}
                    onSelect={setWaterLiter}
                    format={(v) => `${v.toFixed(1)}L`}
                  />
                </CollapsibleBlock>

                <CollapsibleBlock title={`😴 수면 · ${sleepHours}시간 / 목표 ${SLEEP_TARGET}시간`}>
                  <ScaleRow
                    values={SLEEP_HOURS}
                    active={sleepHours}
                    onSelect={setSleepHours}
                    format={(v) => `${v}h`}
                  />
                </CollapsibleBlock>

                <CollapsibleBlock title="🙂 컨디션">
                  <div className="grid grid-cols-5 gap-2">
                    {MOOD_OPTIONS.map((mood) => (
                      <button
                        key={mood.score}
                        type="button"
                        onClick={() => setMoodScore(moodScore === mood.score ? null : mood.score)}
                        className={[
                          "rounded-2xl border-2 py-3 text-3xl transition-colors",
                          moodScore === mood.score
                            ? [DAILY_COLOR.border, "bg-zinc-800"].join(" ")
                            : "border-zinc-700 bg-zinc-800",
                        ].join(" ")}
                      >
                        {mood.icon}
                      </button>
                    ))}
                  </div>
                </CollapsibleBlock>
              </div>
            </Section>

            <Section
              title="🔥 칼로리"
              color={remainingKcal < 0 ? OVER_BUDGET_COLOR : CALORIE_COLOR}
              subtitle={`${remainingKcal >= 0 ? remainingKcal : `-${Math.abs(remainingKcal)}`}kcal 남음`}
            >
              <div className="grid grid-cols-2 gap-2">
                <div className="rounded-2xl bg-zinc-800 p-3">
                  <p className="text-xs font-bold text-zinc-500">섭취 칼로리</p>
                  <p className="mt-1 text-lg font-black text-zinc-100">{totalDietKcal}kcal</p>
                </div>
                <div className="rounded-2xl bg-zinc-800 p-3">
                  <p className="text-xs font-bold text-zinc-500">잔여 칼로리 / 목표 {DAILY_CALORIE_BUDGET}kcal</p>
                  <p
                    className={[
                      "mt-1 text-lg font-black",
                      remainingKcal < 0 ? OVER_BUDGET_COLOR.text : "text-zinc-100",
                    ].join(" ")}
                  >
                    {remainingKcal}kcal
                  </p>
                </div>
              </div>
              <div className="mt-3 h-2 w-full overflow-hidden rounded-full bg-zinc-800">
                <div
                  className={[
                    "h-full rounded-full transition-all",
                    remainingKcal < 0 ? OVER_BUDGET_COLOR.bg : CALORIE_COLOR.bg,
                  ].join(" ")}
                  style={{ width: `${Math.min(100, Math.round((totalDietKcal / DAILY_CALORIE_BUDGET) * 100))}%` }}
                />
              </div>
            </Section>

            <Section title="🍱 식단" color={DIET_COLOR} subtitle={`${totalDietKcal}kcal`}>
              <div className="space-y-4">
                <FoodSection
                  title="🥩 단백질"
                  kcal={proteinKcal}
                  target={proteinTarget}
                  foods={PROTEIN_FOODS}
                  counts={proteinCounts}
                  onChangeCount={onChangeProteinCount}
                  category="protein"
                  customItems={customMealItems}
                  onSaveCustom={updateCustomMealItem}
                  onRemoveCustom={removeCustomMealItem}
                />

                <FoodSection
                  title="🍚 탄수화물"
                  kcal={carbKcal}
                  target={carbTarget}
                  foods={CARB_FOODS}
                  counts={carbCounts}
                  onChangeCount={onChangeCarbCount}
                  category="carb"
                  customItems={customMealItems}
                  onSaveCustom={updateCustomMealItem}
                  onRemoveCustom={removeCustomMealItem}
                />

                <FoodSection
                  title="🥑 지방"
                  kcal={fatKcal}
                  target={fatTarget}
                  foods={FAT_FOODS}
                  counts={fatCounts}
                  onChangeCount={onChangeFatCount}
                  category="fat"
                  customItems={customMealItems}
                  onSaveCustom={updateCustomMealItem}
                  onRemoveCustom={removeCustomMealItem}
                />

                <CollapsibleBlock
                  title={supplementCustomKcal > 0 ? `🫐 보충음식 · ${supplementCustomKcal}kcal` : "🫐 보충음식"}
                >
                  <div className="space-y-3">
                    <div className="flex flex-wrap gap-2">
                      {SUPPLEMENT_FOODS.map((food) => (
                        <Chip
                          key={food.label}
                          label={`${food.label} ${food.unit}`}
                          active={supplementItems.has(food.label)}
                          onClick={() => toggleSupplement(food.label)}
                          color={DIET_COLOR}
                        />
                      ))}
                      {customEntriesByCategory(customMealItems, "supplement").map(({ item, index }) => (
                        <CustomFoodRow
                          key={`${item.name}-${index}`}
                          item={item}
                          color={DIET_COLOR}
                          compact
                          onSave={(entry) => updateCustomMealItem(index, entry)}
                          onRemove={() => removeCustomMealItem(index)}
                        />
                      ))}
                    </div>
                  </div>
                </CollapsibleBlock>

                <CollapsibleBlock title={`🍽 일반식 · ${generalFoodKcal}kcal`}>
                  <div className="space-y-3">
                    <div className="flex flex-wrap gap-2">
                      {customEntriesByCategory(customMealItems, "general").map(({ item, index }) => (
                        <CustomFoodRow
                          key={`${item.name}-${index}`}
                          item={item}
                          color={DIET_COLOR}
                          compact
                          small
                          onSave={(entry) => updateCustomMealItem(index, entry)}
                          onRemove={() => removeCustomMealItem(index)}
                        />
                      ))}
                    </div>

                    {foodHistory.length > 0 && (
                      <div className="rounded-2xl border border-zinc-800 bg-zinc-900 p-3">
                        <p className="text-xs font-bold text-zinc-400">이전에 입력한 음식에서 선택</p>
                        <input
                          value={foodHistoryQuery}
                          onChange={(e) => setFoodHistoryQuery(e.target.value)}
                          placeholder="음식 이름 검색"
                          className="mt-2 w-full rounded-xl border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm font-bold text-zinc-100 placeholder:text-zinc-500 placeholder:font-normal"
                        />
                        {filteredFoodHistory.length === 0 ? (
                          <p className="mt-2 text-xs font-bold text-zinc-600">검색 결과가 없어요.</p>
                        ) : (
                          <div className="mt-2 max-h-40 space-y-1.5 overflow-y-auto pr-1">
                            {filteredFoodHistory.map((item) => (
                              <button
                                key={item.name}
                                type="button"
                                onClick={() => addCustomMealItem(item)}
                                className="flex w-full items-center justify-between rounded-xl border border-zinc-700 bg-zinc-800 px-3 py-2 text-left"
                              >
                                <span className="text-sm font-bold text-zinc-200">{item.name}</span>
                                <span className="shrink-0 text-xs font-bold text-zinc-500">
                                  {item.quantity !== null ? `${item.quantity}${item.unit === "g" ? "g" : "개"} · ` : ""}
                                  {item.totalCalorie}kcal
                                </span>
                              </button>
                            ))}
                          </div>
                        )}
                      </div>
                    )}

                    <CustomFoodForm onAdd={addCustomMealItem} />
                  </div>
                </CollapsibleBlock>
              </div>
            </Section>

            <Section title="🏋 운동" color={WORKOUT_COLOR} subtitle={`${totalWorkoutKcal}kcal`}>
              <div className="space-y-4">
                {(
                  [
                    { key: "strength", title: "💪 근력" },
                    { key: "cardio", title: "🏃 유산소" },
                  ] as const
                ).map((group) => {
                  const totals = workoutBreakdown[group.key];
                  return (
                  <CollapsibleBlock key={group.key} title={`${group.title} · ${totals.minutes}분 · ${totals.kcal}kcal`}>
                    <div className="space-y-2">
                      {WORKOUT_TYPES.filter((w) => w.category === group.key).map((w) => {
                        const suggestion = todaySchedule.suggestions.find((s) => s.type === w.label);
                        const selected = selectedWorkouts.get(w.label);
                        const isSelected = !!selected;

                        return (
                          <div
                            key={w.label}
                            className={[
                              "rounded-2xl border-2 bg-zinc-800 p-3",
                              isSelected ? WORKOUT_COLOR.border : "border-transparent",
                            ].join(" ")}
                          >
                            <div className="flex items-center gap-2">
                              <button
                                type="button"
                                onClick={() => toggleWorkout(w.label, suggestion?.minutes ?? w.defaultMinutes)}
                                className="min-w-0 flex-1 text-left"
                              >
                                <p className="truncate font-bold text-zinc-100">
                                  {isSelected ? "✓ " : suggestion ? "⭐ " : ""}
                                  {w.label}
                                </p>
                                <p className="text-xs text-zinc-500">
                                  {isSelected
                                    ? `${selected.minutes}분 · ${kcalFor(w.label, selected.minutes)}kcal`
                                    : `기본 ${w.defaultMinutes}분`}
                                </p>
                              </button>

                              {isSelected ? (
                                <>
                                  <Stepper
                                    value={selected.minutes}
                                    onChange={(v) => updateWorkoutMinutes(w.label, v)}
                                    suffix="분"
                                    step={5}
                                  />
                                  <button
                                    type="button"
                                    onClick={() => toggleWorkout(w.label, selected.minutes)}
                                    className={[WORKOUT_COLOR.bg, "h-8 w-8 shrink-0 rounded-full text-sm font-black text-zinc-950"].join(" ")}
                                  >
                                    ✕
                                  </button>
                                </>
                              ) : (
                                <button
                                  type="button"
                                  onClick={() => toggleWorkout(w.label, suggestion?.minutes ?? w.defaultMinutes)}
                                  className="shrink-0 rounded-full border-2 border-zinc-700 bg-zinc-900 px-3.5 py-2 text-sm font-bold text-zinc-300"
                                >
                                  선택
                                </button>
                              )}
                            </div>

                            {isSelected && w.subExercises && (
                              <div className="mt-2 flex flex-wrap gap-1.5">
                                {w.subExercises.map((exercise) => (
                                  <button
                                    key={exercise}
                                    type="button"
                                    onClick={() => toggleWorkoutDetail(w.label, exercise)}
                                    className={[
                                      "shrink-0 rounded-full border px-2.5 py-1 text-xs font-bold transition-colors",
                                      selected.details.has(exercise)
                                        ? [WORKOUT_COLOR.border, WORKOUT_COLOR.bg, "text-zinc-950"].join(" ")
                                        : "border-zinc-700 bg-zinc-900 text-zinc-400",
                                    ].join(" ")}
                                  >
                                    {selected.details.has(exercise) && "✓ "}
                                    {exercise}
                                  </button>
                                ))}
                              </div>
                            )}
                          </div>
                        );
                      })}

                      {group.key === "cardio" && (
                        <>
                          {customCardioWorkouts.map((w, index) => (
                            <CustomWorkoutRow
                              key={`${w.name}-${index}`}
                              item={w}
                              color={WORKOUT_COLOR}
                              onSave={(entry) => updateCustomCardioWorkout(index, entry)}
                              onRemove={() => removeCustomCardioWorkout(index)}
                            />
                          ))}

                          <CustomWorkoutForm onAdd={addCustomCardioWorkout} />
                        </>
                      )}
                    </div>
                  </CollapsibleBlock>
                  );
                })}
              </div>

              {workoutDone && (
                <textarea
                  value={workoutComment}
                  onChange={(e) => setWorkoutComment(e.target.value)}
                  placeholder="오늘 운동에 대한 코멘트를 남겨보세요"
                  rows={2}
                  className="mt-4 w-full rounded-2xl border border-zinc-700 bg-zinc-800 p-3 text-sm font-bold text-zinc-100 placeholder:text-zinc-500 placeholder:font-normal"
                />
              )}
            </Section>

            <p className="mt-3 text-center text-xs font-bold text-zinc-600">
              {autoSaveStatus === "saving" && "자동 저장 중..."}
              {autoSaveStatus === "saved" && "✓ 자동 저장됨"}
            </p>

            <Section title="🤖 AI 코치" color={AI_COLOR}>
              <button
                type="button"
                onClick={requestCoaching}
                disabled={coachStatus === "loading"}
                className="w-full rounded-xl border border-zinc-700 bg-zinc-800 py-2 text-xs font-black text-zinc-100 disabled:opacity-50"
              >
                {coachStatus === "loading" ? "코칭 받는 중..." : "🤖 AI 코칭 받기"}
              </button>

              {coachStatus !== "idle" && (
                <div className="mt-4 border-t border-zinc-800 pt-4">
                  <p className="font-bold leading-relaxed text-zinc-100">
                    {coachStatus === "loading" && !coachText
                      ? "코치가 오늘 운동/식단을 분석하고 있습니다..."
                      : coachText}
                  </p>

                  {(coachWorkoutText || coachMealText) && (
                    <div className="mt-4 space-y-3 border-t border-zinc-800 pt-4">
                      {coachWorkoutText && (
                        <div>
                          <p className="text-xs font-black text-blue-400">🏋 운동</p>
                          <p className="mt-1 text-sm font-bold leading-relaxed text-zinc-300">{coachWorkoutText}</p>
                        </div>
                      )}
                      {coachMealText && (
                        <div>
                          <p className="text-xs font-black text-yellow-400">🍱 식단</p>
                          <p className="mt-1 text-sm font-bold leading-relaxed text-zinc-300">{coachMealText}</p>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}
            </Section>
          </>
        )}
      </div>
    </main>
  );
}

function Section({
  title,
  color,
  subtitle,
  collapsible = false,
  defaultOpen = true,
  children,
}: {
  title: string;
  color?: BlockColor;
  subtitle?: string;
  collapsible?: boolean;
  defaultOpen?: boolean;
  children: React.ReactNode;
}) {
  const [icon, ...rest] = title.split(" ");
  const label = rest.join(" ");
  const [open, setOpen] = useState(defaultOpen);
  const showBody = !collapsible || open;

  const header = (
    <div className="flex items-center gap-2">
      <span className="grid h-8 w-8 shrink-0 place-items-center rounded-xl bg-zinc-800 text-base">{icon}</span>
      <h2 className="text-base font-black text-zinc-100">{label}</h2>
    </div>
  );

  return (
    <section
      className={["mt-3 rounded-3xl border bg-zinc-900 p-4 shadow-sm", color ? color.borderSoft : "border-zinc-800"].join(
        " "
      )}
    >
      <div className={["flex items-center justify-between gap-2", showBody ? "mb-3" : ""].join(" ")}>
        {collapsible ? (
          <button type="button" onClick={() => setOpen((v) => !v)} className="flex items-center gap-2 text-left">
            {header}
          </button>
        ) : (
          header
        )}
        <div className="flex items-center gap-2">
          {subtitle && (
            <span className={[color ? color.text : "text-zinc-300", "text-lg font-black"].join(" ")}>{subtitle}</span>
          )}
          {collapsible && (
            <button
              type="button"
              onClick={() => setOpen((v) => !v)}
              className="grid h-8 w-8 shrink-0 place-items-center rounded-xl bg-zinc-800 text-xs font-bold text-zinc-400"
              aria-label={open ? "접기" : "펼치기"}
            >
              {open ? "▲" : "▼"}
            </button>
          )}
        </div>
      </div>
      {showBody && children}
    </section>
  );
}

// 식단 섹션 중 가장 무거운 하위 트리(음식 카탈로그 + 직접입력 목록)라 memo로 감싼다.
// 몸무게/운동 코멘트처럼 무관한 필드를 입력할 때 이 트리 전체가 다시 렌더링되지 않으려면
// props(특히 onChangeCount/onSaveCustom/onRemoveCustom)가 매 렌더 새로 생성되지 않고
// 안정적이어야 하므로, 호출하는 쪽에서 useCallback으로 감싼 함수를 넘긴다.
const FoodSection = memo(function FoodSection({
  title,
  kcal,
  target,
  foods,
  counts,
  onChangeCount,
  category,
  customItems,
  onSaveCustom,
  onRemoveCustom,
}: {
  title: string;
  kcal: number;
  target: number;
  foods: FoodItem[];
  counts: Map<string, number>;
  onChangeCount: (label: string, count: number) => void;
  category: FoodCategory;
  customItems: CustomFoodEntry[];
  onSaveCustom: (index: number, entry: CustomFoodEntry) => void;
  onRemoveCustom: (index: number) => void;
}) {
  return (
    <CollapsibleBlock title={`${title} · ${kcal}kcal / 목표 ${target}kcal`}>
      <div className="space-y-3">
        {foods.map((food) => {
          const amount = counts.get(food.label) ?? 0;
          const itemKcal = foodKcal(food, amount);
          const unitLabel = food.mode === "gram" ? "g" : "개";

          return (
            <div
              key={food.label}
              className={[
                "rounded-2xl border-2 bg-zinc-800 p-3",
                amount > 0 ? DIET_COLOR.border : "border-transparent",
              ].join(" ")}
            >
              <div className="flex items-center justify-between gap-2">
                <p className="font-bold text-zinc-100">{food.label}</p>
                <p className="text-xs text-zinc-500">
                  {food.mode === "gram" ? `100g당 ${food.kcalPer100g}kcal` : `1개당 ${food.kcalPerPiece}kcal`}
                </p>
              </div>
              {amount > 0 && (
                <div className="mt-1 flex items-center justify-between">
                  <p className="text-sm font-bold text-zinc-100">
                    현재섭취 {amount}
                    {unitLabel} / {itemKcal}kcal
                  </p>
                  <button
                    type="button"
                    onClick={() => onChangeCount(food.label, 0)}
                    className="text-xs font-bold text-zinc-500 underline"
                  >
                    초기화
                  </button>
                </div>
              )}
              <div className="mt-2">
                {food.mode === "gram" ? (
                  <GramRoller
                    onAdd={(v) => onChangeCount(food.label, amount + v)}
                    color={DIET_COLOR}
                  />
                ) : (
                  <Stepper
                    value={amount}
                    onChange={(v) => onChangeCount(food.label, v)}
                    suffix="개"
                    step={1}
                  />
                )}
              </div>
            </div>
          );
        })}

        {customEntriesByCategory(customItems, category).map(({ item, index }) => (
          <CustomFoodRow
            key={`${item.name}-${index}`}
            item={item}
            color={DIET_COLOR}
            onSave={(entry) => onSaveCustom(index, entry)}
            onRemove={() => onRemoveCustom(index)}
          />
        ))}
      </div>
    </CollapsibleBlock>
  );
});

// CustomFoodForm(추가)과 CustomFoodRow(수정)가 공유하는 입력 필드 UI.
function CustomFoodFields({
  name,
  setName,
  category,
  setCategory,
  unit,
  setUnit,
  quantityInput,
  setQuantityInput,
  calorieInput,
  setCalorieInput,
  kcalPer100g,
  color,
}: {
  name: string;
  setName: (v: string) => void;
  category: FoodCategory;
  setCategory: (v: FoodCategory) => void;
  unit: "g" | "count";
  setUnit: (v: "g" | "count") => void;
  quantityInput: string;
  setQuantityInput: (v: string) => void;
  calorieInput: string;
  setCalorieInput: (v: string) => void;
  kcalPer100g: number | null;
  color: BlockColor;
}) {
  return (
    <>
      <input
        value={name}
        onChange={(e) => setName(e.target.value)}
        placeholder="음식 이름"
        className="w-full rounded-xl border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm font-bold text-zinc-100 placeholder:text-zinc-500 placeholder:font-normal"
      />

      <div className="flex gap-1.5 overflow-x-auto pb-0.5">
        {FOOD_CATEGORY_OPTIONS.map((opt) => (
          <button
            key={opt.value}
            type="button"
            onClick={() => setCategory(opt.value)}
            className={[
              "shrink-0 rounded-full border px-3 py-1.5 text-xs font-bold transition-colors",
              category === opt.value
                ? [color.border, color.bg, "text-zinc-950"].join(" ")
                : "border-zinc-700 bg-zinc-800 text-zinc-400",
            ].join(" ")}
          >
            {opt.label}
          </button>
        ))}
      </div>

      <div className="flex gap-2">
        <div className="flex flex-1 rounded-xl border border-zinc-700 bg-zinc-800 p-1">
          <button
            type="button"
            onClick={() => setUnit("g")}
            className={["flex-1 rounded-lg py-1.5 text-xs font-black transition-colors", unit === "g" ? [color.bg, "text-zinc-950"].join(" ") : "text-zinc-400"].join(" ")}
          >
            그램(g)
          </button>
          <button
            type="button"
            onClick={() => setUnit("count")}
            className={["flex-1 rounded-lg py-1.5 text-xs font-black transition-colors", unit === "count" ? [color.bg, "text-zinc-950"].join(" ") : "text-zinc-400"].join(" ")}
          >
            개수(개)
          </button>
        </div>

        <input
          type="number"
          inputMode="decimal"
          min={0}
          value={quantityInput}
          onChange={(e) => setQuantityInput(e.target.value)}
          placeholder={unit === "g" ? "g (선택)" : "개수 (선택)"}
          className="w-24 rounded-xl border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm font-bold text-zinc-100 placeholder:text-zinc-500 placeholder:font-normal"
        />
      </div>

      <div className="flex items-center gap-2">
        <input
          type="number"
          inputMode="decimal"
          min={0}
          value={calorieInput}
          onChange={(e) => setCalorieInput(e.target.value)}
          placeholder="총 칼로리 (kcal)"
          className="flex-1 rounded-xl border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm font-bold text-zinc-100 placeholder:text-zinc-500 placeholder:font-normal"
        />
        <div className="shrink-0 rounded-xl bg-zinc-800 px-3 py-2 text-right">
          <p className="text-[10px] font-bold text-zinc-500">100g당</p>
          <p className="text-sm font-black text-zinc-100">{kcalPer100g !== null ? `${kcalPer100g}kcal` : "-"}</p>
        </div>
      </div>
    </>
  );
}

function useCustomFoodFormState(initial?: CustomFoodEntry) {
  const [name, setName] = useState(initial?.name ?? "");
  const [category, setCategory] = useState<FoodCategory>(initial?.category ?? "general");
  const [unit, setUnit] = useState<"g" | "count">(initial?.unit ?? "g");
  const [quantityInput, setQuantityInput] = useState(initial?.quantity != null ? String(initial.quantity) : "");
  const [calorieInput, setCalorieInput] = useState(initial ? String(initial.totalCalorie) : "");

  const quantity = quantityInput.trim() === "" ? null : Number(quantityInput);
  const totalCalorie = calorieInput.trim() === "" ? null : Number(calorieInput);
  const kcalPer100g = caloriesPer100g(unit, quantity, totalCalorie);

  const quantityValid = quantity === null || !Number.isNaN(quantity);
  const calorieValid = totalCalorie !== null && !Number.isNaN(totalCalorie);
  const canSubmit = name.trim() !== "" && calorieValid && quantityValid;

  function reset(entry?: CustomFoodEntry) {
    setName(entry?.name ?? "");
    setCategory(entry?.category ?? "general");
    setUnit(entry?.unit ?? "g");
    setQuantityInput(entry?.quantity != null ? String(entry.quantity) : "");
    setCalorieInput(entry ? String(entry.totalCalorie) : "");
  }

  return {
    name, setName, category, setCategory, unit, setUnit, quantityInput, setQuantityInput, calorieInput, setCalorieInput,
    quantity, totalCalorie, kcalPer100g, canSubmit, reset,
  };
}

function CustomFoodForm({ onAdd }: { onAdd: (entry: CustomFoodEntry) => void }) {
  const f = useCustomFoodFormState();

  function handleAdd() {
    if (!f.canSubmit || f.totalCalorie === null) return;
    onAdd({ name: f.name.trim(), unit: f.unit, quantity: f.quantity, totalCalorie: f.totalCalorie, kcalPer100g: f.kcalPer100g, category: f.category });
    f.reset();
  }

  return (
    <div className="rounded-2xl border border-dashed border-zinc-700 bg-zinc-900 p-3">
      <p className="text-xs font-bold text-zinc-400">직접입력 (카탈로그에 없는 음식)</p>

      <div className="mt-2 space-y-2">
        <CustomFoodFields
          name={f.name} setName={f.setName}
          category={f.category} setCategory={f.setCategory}
          unit={f.unit} setUnit={f.setUnit}
          quantityInput={f.quantityInput} setQuantityInput={f.setQuantityInput}
          calorieInput={f.calorieInput} setCalorieInput={f.setCalorieInput}
          kcalPer100g={f.kcalPer100g}
          color={DIET_COLOR}
        />

        <button
          type="button"
          onClick={handleAdd}
          disabled={!f.canSubmit}
          className={[DIET_COLOR.bg, "w-full rounded-xl py-2 text-sm font-black text-zinc-950 disabled:opacity-40"].join(" ")}
        >
          + 추가하기
        </button>
      </div>
    </div>
  );
}

function CustomFoodRow({
  item,
  color,
  onSave,
  onRemove,
  compact = false,
  small = false,
}: {
  item: CustomFoodEntry;
  color: BlockColor;
  onSave: (entry: CustomFoodEntry) => void;
  onRemove: () => void;
  compact?: boolean;
  small?: boolean;
}) {
  const [editing, setEditing] = useState(false);
  const f = useCustomFoodFormState(item);

  function startEdit() {
    f.reset(item);
    setEditing(true);
  }

  function handleSave() {
    if (!f.canSubmit || f.totalCalorie === null) return;
    onSave({ name: f.name.trim(), unit: f.unit, quantity: f.quantity, totalCalorie: f.totalCalorie, kcalPer100g: f.kcalPer100g, category: f.category });
    setEditing(false);
  }

  if (!editing && compact) {
    // 보충음식/일반식은 카탈로그가 칩(Chip) 형태라, 직접입력 항목도 같은 크기의 칩으로 보여준다.
    return (
      <button
        type="button"
        onClick={startEdit}
        className={[
          "inline-flex shrink-0 items-center gap-1.5 rounded-full border-2 bg-zinc-800 font-bold text-zinc-100",
          small ? "px-3 py-1.5 text-xs" : "px-4 py-2.5 text-sm",
          color.border,
        ].join(" ")}
      >
        <span>
          {item.name} · {item.totalCalorie}kcal
        </span>
        <span
          role="button"
          tabIndex={-1}
          onClick={(e) => {
            e.stopPropagation();
            onRemove();
          }}
          className="text-zinc-400"
        >
          ✕
        </span>
      </button>
    );
  }

  if (!editing) {
    return (
      <div className={["rounded-2xl border-2 bg-zinc-800 p-3", color.border].join(" ")}>
        <div className="flex items-center justify-between gap-2">
          <p className="font-bold text-zinc-100">{item.name}</p>
          <div className="flex shrink-0 gap-3">
            <button type="button" onClick={startEdit} className="text-xs font-bold text-zinc-400 underline">
              수정
            </button>
            <button type="button" onClick={onRemove} className="text-xs font-bold text-zinc-500 underline">
              삭제
            </button>
          </div>
        </div>
        <p className="mt-1 text-sm font-bold text-zinc-100">
          {item.quantity !== null ? `${item.quantity}${item.unit === "g" ? "g" : "개"} / ` : ""}
          {item.totalCalorie}kcal
          {item.kcalPer100g !== null ? ` · 100g당 ${item.kcalPer100g}kcal` : ""}
        </p>
      </div>
    );
  }

  return (
    <div className={["rounded-2xl border-2 bg-zinc-900 p-3", compact ? "w-full" : "", color.border].join(" ")}>
      <div className="space-y-2">
        <CustomFoodFields
          name={f.name} setName={f.setName}
          category={f.category} setCategory={f.setCategory}
          unit={f.unit} setUnit={f.setUnit}
          quantityInput={f.quantityInput} setQuantityInput={f.setQuantityInput}
          calorieInput={f.calorieInput} setCalorieInput={f.setCalorieInput}
          kcalPer100g={f.kcalPer100g}
          color={color}
        />

        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => setEditing(false)}
            className="flex-1 rounded-xl border border-zinc-700 py-2 text-sm font-black text-zinc-300"
          >
            취소
          </button>
          <button
            type="button"
            onClick={handleSave}
            disabled={!f.canSubmit}
            className={[color.bg, "flex-1 rounded-xl py-2 text-sm font-black text-zinc-950 disabled:opacity-40"].join(" ")}
          >
            저장
          </button>
        </div>
      </div>
    </div>
  );
}

// CustomWorkoutForm(추가)과 CustomWorkoutRow(수정)가 공유하는 입력 필드 UI.
function CustomWorkoutFields({
  name,
  setName,
  minutesInput,
  setMinutesInput,
  calorieInput,
  setCalorieInput,
}: {
  name: string;
  setName: (v: string) => void;
  minutesInput: string;
  setMinutesInput: (v: string) => void;
  calorieInput: string;
  setCalorieInput: (v: string) => void;
}) {
  return (
    <>
      <input
        value={name}
        onChange={(e) => setName(e.target.value)}
        placeholder="운동 이름 (예: 수영, 조깅)"
        className="w-full rounded-xl border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm font-bold text-zinc-100 placeholder:text-zinc-500 placeholder:font-normal"
      />

      <div className="flex items-center gap-2">
        <input
          type="number"
          inputMode="numeric"
          min={0}
          value={minutesInput}
          onChange={(e) => setMinutesInput(e.target.value)}
          placeholder="시간 (분)"
          className="flex-1 rounded-xl border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm font-bold text-zinc-100 placeholder:text-zinc-500 placeholder:font-normal"
        />
        <input
          type="number"
          inputMode="numeric"
          min={0}
          value={calorieInput}
          onChange={(e) => setCalorieInput(e.target.value)}
          placeholder="소모 칼로리(kcal)"
          className="flex-1 rounded-xl border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm font-bold text-zinc-100 placeholder:text-zinc-500 placeholder:font-normal"
        />
      </div>
    </>
  );
}

function useCustomWorkoutFormState(initial?: CustomWorkoutEntry) {
  const [name, setName] = useState(initial?.name ?? "");
  const [minutesInput, setMinutesInput] = useState(initial ? String(initial.minutes) : "");
  const [calorieInput, setCalorieInput] = useState(initial ? String(initial.calorieEstimate) : "");

  const minutes = minutesInput.trim() === "" ? null : Number(minutesInput);
  const calorieEstimate = calorieInput.trim() === "" ? null : Number(calorieInput);

  const minutesValid = minutes !== null && !Number.isNaN(minutes) && minutes > 0;
  const calorieValid = calorieEstimate !== null && !Number.isNaN(calorieEstimate) && calorieEstimate >= 0;
  const canSubmit = name.trim() !== "" && minutesValid && calorieValid;

  function reset(entry?: CustomWorkoutEntry) {
    setName(entry?.name ?? "");
    setMinutesInput(entry ? String(entry.minutes) : "");
    setCalorieInput(entry ? String(entry.calorieEstimate) : "");
  }

  return { name, setName, minutesInput, setMinutesInput, calorieInput, setCalorieInput, minutes, calorieEstimate, canSubmit, reset };
}

function CustomWorkoutForm({ onAdd }: { onAdd: (entry: CustomWorkoutEntry) => void }) {
  const f = useCustomWorkoutFormState();

  function handleAdd() {
    if (!f.canSubmit || f.minutes === null || f.calorieEstimate === null) return;
    onAdd({ name: f.name.trim(), minutes: f.minutes, calorieEstimate: f.calorieEstimate });
    f.reset();
  }

  return (
    <div className="rounded-2xl border border-dashed border-zinc-700 bg-zinc-900 p-3">
      <p className="text-xs font-bold text-zinc-400">직접입력 (목록에 없는 운동)</p>

      <div className="mt-2 space-y-2">
        <CustomWorkoutFields
          name={f.name} setName={f.setName}
          minutesInput={f.minutesInput} setMinutesInput={f.setMinutesInput}
          calorieInput={f.calorieInput} setCalorieInput={f.setCalorieInput}
        />

        <button
          type="button"
          onClick={handleAdd}
          disabled={!f.canSubmit}
          className={[WORKOUT_COLOR.bg, "w-full rounded-xl py-2 text-sm font-black text-zinc-950 disabled:opacity-40"].join(" ")}
        >
          + 추가하기
        </button>
      </div>
    </div>
  );
}

function CustomWorkoutRow({
  item,
  color,
  onSave,
  onRemove,
}: {
  item: CustomWorkoutEntry;
  color: BlockColor;
  onSave: (entry: CustomWorkoutEntry) => void;
  onRemove: () => void;
}) {
  const [editing, setEditing] = useState(false);
  const f = useCustomWorkoutFormState(item);

  function startEdit() {
    f.reset(item);
    setEditing(true);
  }

  function handleSave() {
    if (!f.canSubmit || f.minutes === null || f.calorieEstimate === null) return;
    onSave({ name: f.name.trim(), minutes: f.minutes, calorieEstimate: f.calorieEstimate });
    setEditing(false);
  }

  if (!editing) {
    return (
      <div className={["rounded-2xl border-2 bg-zinc-800 p-3", color.border].join(" ")}>
        <div className="flex items-center justify-between gap-2">
          <div>
            <p className="font-bold text-zinc-100">{item.name}</p>
            <p className="text-xs text-zinc-500">
              {item.minutes}분 · {item.calorieEstimate}kcal
            </p>
          </div>
          <div className="flex shrink-0 gap-3">
            <button type="button" onClick={startEdit} className="text-xs font-bold text-zinc-400 underline">
              수정
            </button>
            <button type="button" onClick={onRemove} className="text-xs font-bold text-zinc-500 underline">
              삭제
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={["rounded-2xl border-2 bg-zinc-900 p-3", color.border].join(" ")}>
      <div className="space-y-2">
        <CustomWorkoutFields
          name={f.name} setName={f.setName}
          minutesInput={f.minutesInput} setMinutesInput={f.setMinutesInput}
          calorieInput={f.calorieInput} setCalorieInput={f.setCalorieInput}
        />

        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => setEditing(false)}
            className="flex-1 rounded-xl border border-zinc-700 py-2 text-sm font-black text-zinc-300"
          >
            취소
          </button>
          <button
            type="button"
            onClick={handleSave}
            disabled={!f.canSubmit}
            className={[color.bg, "flex-1 rounded-xl py-2 text-sm font-black text-zinc-950 disabled:opacity-40"].join(" ")}
          >
            저장
          </button>
        </div>
      </div>
    </div>
  );
}

function CollapsibleBlock({ title, children }: { title: string; children: React.ReactNode }) {
  const [open, setOpen] = useState(false);

  return (
    <div className="border-t border-zinc-800 pt-4 first:border-t-0 first:pt-0">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center justify-between text-left"
      >
        <p className="text-sm font-bold text-zinc-300">{title}</p>
        <span className="text-xs font-bold text-zinc-500">{open ? "▲ 접기" : "▼ 펼치기"}</span>
      </button>
      {open && <div className="mt-2">{children}</div>}
    </div>
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

const CHART_ACCENT = "#e5e7eb"; // zinc-200, monotone chart accent

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
              done === true ? "bg-[var(--pop-bg)]" : done === false ? "bg-zinc-700" : "bg-zinc-900",
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
  color = DAILY_COLOR,
}: {
  label: string;
  active: boolean;
  onClick: () => void;
  tone?: "default" | "warn";
  color?: BlockColor;
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
            : [color.border, color.bg, "text-zinc-950"].join(" ")
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
  color = DAILY_COLOR,
}: {
  values: number[];
  active: number;
  onSelect: (value: number) => void;
  format: (value: number) => string;
  color?: BlockColor;
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
              ? [color.border, color.bg, "text-zinc-950"].join(" ")
              : "border-zinc-700 bg-zinc-800 text-zinc-300",
          ].join(" ")}
        >
          {format(value)}
        </button>
      ))}
    </div>
  );
}

const GRAM_ROLLER_ITEM_HEIGHT = 36;

function GramRoller({
  onAdd,
  color,
  values = GRAM_STEPS,
}: {
  onAdd: (amount: number) => void;
  color: BlockColor;
  values?: number[];
}) {
  const [picked, setPicked] = useState(values[9] ?? values[0]);
  const containerRef = useRef<HTMLDivElement>(null);
  const scrollTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    const idx = values.indexOf(picked);
    if (containerRef.current && idx >= 0) {
      containerRef.current.scrollTop = idx * GRAM_ROLLER_ITEM_HEIGHT;
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function handleScroll() {
    if (scrollTimer.current) clearTimeout(scrollTimer.current);
    scrollTimer.current = setTimeout(() => {
      if (!containerRef.current) return;
      const idx = Math.round(containerRef.current.scrollTop / GRAM_ROLLER_ITEM_HEIGHT);
      const v = values[Math.min(Math.max(idx, 0), values.length - 1)];
      if (v !== undefined) setPicked(v);
    }, 80);
  }

  return (
    <div className="flex items-center gap-3">
      <div className="relative h-[108px] w-24 shrink-0 overflow-hidden rounded-xl border border-zinc-700 bg-zinc-900">
        <div
          ref={containerRef}
          onScroll={handleScroll}
          className="h-full snap-y snap-mandatory overflow-y-auto [-ms-overflow-style:none] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
        >
          <div style={{ height: GRAM_ROLLER_ITEM_HEIGHT }} />
          {values.map((v) => (
            <div
              key={v}
              className="flex snap-center items-center justify-center text-sm font-bold text-zinc-300"
              style={{ height: GRAM_ROLLER_ITEM_HEIGHT }}
            >
              {v}g
            </div>
          ))}
          <div style={{ height: GRAM_ROLLER_ITEM_HEIGHT }} />
        </div>
        <div
          className={["pointer-events-none absolute inset-x-0 top-1/2 h-9 -translate-y-1/2 border-y-2", color.border].join(
            " "
          )}
        />
      </div>
      <button
        type="button"
        onClick={() => onAdd(picked)}
        className={[color.bg, "shrink-0 rounded-2xl px-4 py-2.5 text-sm font-black text-zinc-950"].join(" ")}
      >
        +{picked}g 담기
      </button>
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
