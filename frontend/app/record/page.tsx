"use client";

import { useState } from "react";

const readyLevels = [
  { label: "ELITE", icon: "🔵", score: 100, text: "최상의 컨디션" },
  { label: "READY", icon: "🟢", score: 90, text: "계획대로 수행" },
  { label: "NORMAL", icon: "🟡", score: 75, text: "무난하게 이어감" },
  { label: "CARE", icon: "🟠", score: 60, text: "관리 필요" },
  { label: "RECOVERY", icon: "🔴", score: 40, text: "회복 우선" },
];

const workoutOptions = [
  "풋살",
  "PT 상체",
  "PT 하체",
  "개인운동 어깨강화",
  "개인운동 키퍼체력",
  "유산소 자전거 30분",
  "유산소 천국의 계단 20분",
  "폼롤러 스트레칭",
];

const waterOptions = ["0L", "1.0L", "1.5L", "2.0L", "2.5L"];
const proteinOptions = ["0g", "40g", "60g", "80g", "100g"];
const sleepOptions = ["0h", "4h", "5h", "6h", "7h"];

function localToday() {
  const now = new Date();
  const offset = now.getTimezoneOffset() * 60000;
  return new Date(now.getTime() - offset).toISOString().slice(0, 10);
}

export default function RecordPage() {
  const [recordDate, setRecordDate] = useState(localToday());
  const [level, setLevel] = useState("NORMAL");
  const [morningMed, setMorningMed] = useState(false);
  const [eveningMed, setEveningMed] = useState(false);

  const [selectedWorkouts, setSelectedWorkouts] = useState<string[]>([]);
  const [selectedWater, setSelectedWater] = useState("2.5L");
  const [selectedProtein, setSelectedProtein] = useState("100g");
  const [selectedSleep, setSelectedSleep] = useState("7h");

  const [memo, setMemo] = useState("");
  const [coachNote, setCoachNote] = useState("");
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");

  const selectedLevel =
    readyLevels.find((item) => item.label === level) ?? readyLevels[2];

  function toggleItem(
    value: string,
    selected: string[],
    setter: (value: string[]) => void
  ) {
    if (selected.includes(value)) {
      setter(selected.filter((item) => item !== value));
    } else {
      setter([...selected, value]);
    }
  }

  async function saveRecord() {
    setSaving(true);
    setMessage("");

    const completedWorkout = selectedWorkouts.join(", ");
    const bikeMinutes = selectedWorkouts.includes("유산소 자전거 30분") ? 30 : 0;

    const mergedMemo = [
      memo ? `[메모]\n${memo}` : "",
      coachNote ? `[코치 피드백]\n${coachNote}` : "",
    ]
      .filter(Boolean)
      .join("\n\n");

    const payload = {
      record_date: recordDate,
      score: selectedLevel.score,
      grade: selectedLevel.label,
      mood_score: levelToMoodScore(selectedLevel.label),
      memo: mergedMemo,
      morning_med_taken: morningMed,
      evening_med_taken: eveningMed,
      medication_note: buildMedicationNote(morningMed, eveningMed),
      body: {
        water_liter: parseNumber(selectedWater),
        protein_gram: parseNumber(selectedProtein),
        binge_yn: false,
      },
      workout: {
        planned_workout: completedWorkout || null,
        completed_workout: completedWorkout || null,
        bike_minutes: bikeMinutes,
        workout_done_yn: selectedWorkouts.length > 0,
      },
      meal: null,
      sleep: {
        sleep_hours: parseNumber(selectedSleep),
        sleep_quality_score: levelToSleepScore(selectedLevel.label),
        wake_condition: selectedLevel.label,
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
        setMessage(`저장 실패: ${JSON.stringify(data)}`);
        return;
      }

      setMessage("저장 완료. 오늘도 Journey는 이어졌습니다.");

      setTimeout(() => {
        window.location.href = `/?record_date=${recordDate}`;
      }, 700);
    } catch (error) {
      console.error(error);
      setMessage(`저장 실패: ${String(error)}`);
    } finally {
      setSaving(false);
    }
  }

  return (
    <main className="min-h-screen bg-[#f4f1ec] pb-36 text-zinc-900">
      <div className="mx-auto max-w-5xl p-4 md:p-6">
        <header className="rounded-3xl bg-slate-900 p-6 text-white shadow-lg">
          <h1 className="text-3xl font-black">🧤 GK21 Daily Check v1</h1>
          <p className="mt-2 font-bold text-slate-300">
            저장 + 피드백 + 5단계 컨디션 라벨
          </p>
        </header>

        <div className="mt-5 grid gap-4 md:grid-cols-2">
          <Card title="📅 오늘 기록">
            <Field label="날짜">
              <input
                type="date"
                value={recordDate}
                onChange={(event) => setRecordDate(event.target.value)}
                className="input"
              />
            </Field>

            <Field label="오늘 상태">
              <select
                value={level}
                onChange={(event) => setLevel(event.target.value)}
                className="input"
              >
                {readyLevels.map((item) => (
                  <option key={item.label} value={item.label}>
                    {item.icon} {item.label} - {item.text}
                  </option>
                ))}
              </select>
            </Field>
          </Card>

          <Card title="💊 약">
            <div className="grid grid-cols-2 gap-3">
              <Toggle
                label="☀️ 아침약"
                active={morningMed}
                onClick={() => setMorningMed(!morningMed)}
              />
              <Toggle
                label="🌙 저녁약"
                active={eveningMed}
                onClick={() => setEveningMed(!eveningMed)}
              />
            </div>
          </Card>

          <Card title="🏋 운동">
            <SelectList
              options={workoutOptions}
              selected={selectedWorkouts}
              onToggle={(value) =>
                toggleItem(value, selectedWorkouts, setSelectedWorkouts)
              }
            />
          </Card>

          <Card title="💧 수분">
            <SingleSelectList
              options={waterOptions}
              selected={selectedWater}
              onSelect={setSelectedWater}
            />
          </Card>

          <Card title="🥩 단백질">
            <SingleSelectList
              options={proteinOptions}
              selected={selectedProtein}
              onSelect={setSelectedProtein}
            />
          </Card>

          <Card title="😴 수면">
            <SingleSelectList
              options={sleepOptions}
              selected={selectedSleep}
              onSelect={setSelectedSleep}
            />
          </Card>

          <Card title="📝 오늘 메모">
            <textarea
              value={memo}
              onChange={(event) => setMemo(event.target.value)}
              className="textarea"
              placeholder="오늘 한 줄만 남겨도 충분합니다."
            />
          </Card>

          <Card title="🧑‍🏫 코치 피드백 저장">
            <textarea
              value={coachNote}
              onChange={(event) => setCoachNote(event.target.value)}
              className="textarea"
              placeholder="AI 코치 피드백이나 직접 남기고 싶은 피드백을 저장합니다."
            />
          </Card>
        </div>

        {message && (
          <p className="mt-4 rounded-2xl bg-white p-4 text-center text-sm font-black shadow-sm">
            {message}
          </p>
        )}
      </div>

      <div className="fixed bottom-20 left-0 right-0 z-40 bg-[#f4f1ec]/95 px-4 py-3 backdrop-blur">
        <div className="mx-auto max-w-5xl">
          <button
            type="button"
            onClick={saveRecord}
            disabled={saving}
            className="w-full rounded-2xl bg-slate-900 py-4 text-lg font-black text-white shadow-lg disabled:opacity-50"
          >
            {saving ? "저장 중..." : "저장하기"}
          </button>
        </div>
      </div>

      <style jsx>{`
        .input {
          width: 100%;
          border: 1px solid #ddd6ce;
          border-radius: 12px;
          padding: 12px;
          background: #fff;
          font-weight: 800;
        }
        .textarea {
          width: 100%;
          min-height: 120px;
          border: 1px solid #ddd6ce;
          border-radius: 12px;
          padding: 12px;
          background: #fff;
          font-weight: 700;
        }
      `}</style>
    </main>
  );
}

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="rounded-3xl border border-[#ddd6ce] bg-white p-5 shadow-sm">
      <h2 className="mb-4 text-xl font-black">{title}</h2>
      {children}
    </section>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="mt-3 block">
      <p className="mb-2 text-sm font-black text-zinc-500">{label}</p>
      {children}
    </label>
  );
}

function SelectList({
  options,
  selected,
  onToggle,
}: {
  options: string[];
  selected: string[];
  onToggle: (value: string) => void;
}) {
  return (
    <div className="grid gap-2">
      {options.map((item) => (
        <Toggle
          key={item}
          label={item}
          active={selected.includes(item)}
          onClick={() => onToggle(item)}
        />
      ))}
    </div>
  );
}

function SingleSelectList({
  options,
  selected,
  onSelect,
}: {
  options: string[];
  selected: string;
  onSelect: (value: string) => void;
}) {
  return (
    <div className="grid gap-2">
      {options.map((item) => (
        <Toggle
          key={item}
          label={item}
          active={selected === item}
          onClick={() => onSelect(item)}
        />
      ))}
    </div>
  );
}

function Toggle({
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
        "rounded-2xl border p-4 text-center text-base font-black",
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

function parseNumber(value: string) {
  return Number(value.replace(/[^\d.]/g, "") || 0);
}

function levelToMoodScore(level: string) {
  if (level === "ELITE") return 5;
  if (level === "READY") return 5;
  if (level === "NORMAL") return 4;
  if (level === "CARE") return 3;
  return 2;
}

function levelToSleepScore(level: string) {
  if (level === "ELITE") return 95;
  if (level === "READY") return 85;
  if (level === "NORMAL") return 75;
  if (level === "CARE") return 60;
  return 45;
}

function buildMedicationNote(morning: boolean, evening: boolean) {
  if (morning && evening) return "아침약, 저녁약 복용 완료";
  if (morning && !evening) return "아침약 완료, 저녁약 체크 필요";
  if (!morning && evening) return "저녁약 완료, 아침약 체크 필요";
  return "약 체크 필요";
}
