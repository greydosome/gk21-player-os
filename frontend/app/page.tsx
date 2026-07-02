import Header from "@/components/Header";
import TodayCard from "@/components/TodayCard";
import GKReadyCard from "@/components/GKReadyCard";
import MissionCard from "@/components/MissionCard";
import AICoachCard from "@/components/AICoachCard";
import DashboardAccordion from "@/components/DashboardAccordion";
import PhilosophyCard from "@/components/PhilosophyCard";

async function getDashboard(recordDate?: string) {
  const url = recordDate
    ? `http://127.0.0.1:8000/api/dashboard?record_date=${recordDate}`
    : "http://127.0.0.1:8000/api/dashboard";

  const res = await fetch(url, {
    cache: "no-store",
  });

  if (!res.ok) {
    throw new Error("Dashboard API 호출 실패");
  }

  return res.json();
}

export default async function Home({
  searchParams,
}: {
  searchParams?: { record_date?: string };
}) {
  const data = await getDashboard(searchParams?.record_date);

  if (!data.dashboard) {
    return (
      <main className="min-h-screen bg-[#f4f1ec] text-zinc-900">
        <div className="mx-auto max-w-3xl px-4 py-5">
          <Header />

          <section className="mt-5 rounded-2xl border border-[#ddd6ce] bg-white p-6 shadow-sm">
            <p className="text-sm font-bold text-zinc-500">
              {data.record_date}
            </p>

            <h1 className="mt-3 text-2xl font-black">
              아직 오늘 기록이 없습니다.
            </h1>

            <p className="mt-3 font-bold text-zinc-600">
              오늘 체크를 저장하면 GK READY와 코치 피드백이 표시됩니다.
            </p>

            <a
              href="/record"
              className="mt-5 block rounded-2xl bg-slate-900 py-4 text-center text-lg font-black text-white"
            >
              오늘 체크하러 가기
            </a>
          </section>

          <PhilosophyCard philosophy={data.philosophy} />
        </div>
      </main>
    );
  }

  const dashboard = data.dashboard;

  return (
    <main className="min-h-screen bg-[#f4f1ec] text-zinc-900">
      <div className="mx-auto max-w-3xl px-4 py-5">
        <Header />
        <TodayCard today={dashboard} />
        <GKReadyCard ai={data.ai} />
        <MissionCard missions={data.missions ?? []} />
        <AICoachCard ai={data.ai} />
        <DashboardAccordion dashboard={dashboard} ai={data.ai} />
        <PhilosophyCard philosophy={data.philosophy} />
      </div>
    </main>
  );
}
