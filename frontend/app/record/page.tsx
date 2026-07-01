"use client";

import { useState } from "react";

export default function RecordPage() {
  const [morningMed, setMorningMed] = useState(false);
  const [eveningMed, setEveningMed] = useState(false);
  const [workout, setWorkout] = useState(false);

  return (
    <main className="min-h-screen bg-[#f4f1ec] pb-28">
      <div className="mx-auto max-w-md space-y-5 p-5">

        <h1 className="text-3xl font-black">
          📝 오늘 체크
        </h1>

        {/* 약 */}

        <section className="rounded-2xl bg-white p-5 shadow-sm">

          <h2 className="mb-4 text-xl font-bold">
            💊 약
          </h2>

          <label className="flex justify-between py-3">
            <span>아침약</span>

            <input
              type="checkbox"
              checked={morningMed}
              onChange={() => setMorningMed(!morningMed)}
            />
          </label>

          <label className="flex justify-between py-3">
            <span>저녁약</span>

            <input
              type="checkbox"
              checked={eveningMed}
              onChange={() => setEveningMed(!eveningMed)}
            />
          </label>

        </section>

        {/* 운동 */}

        <section className="rounded-2xl bg-white p-5 shadow-sm">

          <h2 className="mb-4 text-xl font-bold">
            🏋 운동
          </h2>

          <label className="flex justify-between py-3">

            <span>운동 완료</span>

            <input
              type="checkbox"
              checked={workout}
              onChange={() => setWorkout(!workout)}
            />

          </label>

          <input
            type="number"
            placeholder="자전거 (분)"
            className="mt-3 w-full rounded-xl border p-3"
          />

        </section>

        {/* 물 */}

        <section className="rounded-2xl bg-white p-5 shadow-sm">

          <h2 className="mb-4 text-xl font-bold">
            💧 물
          </h2>

          <input
            type="number"
            step="0.1"
            placeholder="3.0L"
            className="w-full rounded-xl border p-3"
          />

        </section>

        {/* 단백질 */}

        <section className="rounded-2xl bg-white p-5 shadow-sm">

          <h2 className="mb-4 text-xl font-bold">
            🥩 단백질
          </h2>

          <input
            type="number"
            placeholder="180g"
            className="w-full rounded-xl border p-3"
          />

        </section>

        {/* 수면 */}

        <section className="rounded-2xl bg-white p-5 shadow-sm">

          <h2 className="mb-4 text-xl font-bold">
            😴 수면
          </h2>

          <input
            type="number"
            step="0.5"
            placeholder="7.5시간"
            className="w-full rounded-xl border p-3"
          />

        </section>

        {/* 기분 */}

        <section className="rounded-2xl bg-white p-5 shadow-sm">

          <h2 className="mb-4 text-xl font-bold">
            😊 오늘 기분
          </h2>

          <div className="flex justify-around text-4xl">

            😀 😐 😞

          </div>

        </section>

        {/* 메모 */}

        <section className="rounded-2xl bg-white p-5 shadow-sm">

          <h2 className="mb-4 text-xl font-bold">
            📝 메모
          </h2>

          <textarea
            rows={4}
            className="w-full rounded-xl border p-3"
          />

        </section>

        <button
          className="w-full rounded-2xl bg-slate-900 py-4 text-lg font-bold text-white"
        >
          저장하기
        </button>

      </div>
    </main>
  );
}
