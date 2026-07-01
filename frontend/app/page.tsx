import Header from "@/components/Header";
import TodayCard from "@/components/TodayCard";
import ScoreCard from "@/components/ScoreCard";
import GKReadyCard from "@/components/GKReadyCard";
import MissionCard from "@/components/MissionCard";
import AICoachCard from "@/components/AICoachCard";
import DashboardAccordion from "@/components/DashboardAccordion";
import PhilosophyCard from "@/components/PhilosophyCard";

async function getDashboard() {
  const res = await fetch(
    "http://127.0.0.1:8000/api/dashboard?record_date=2026-06-29",
    { cache: "no-store" }
  );

  if (!res.ok) {
    throw new Error("Dashboard API 호출 실패");
  }

  return res.json();
}

export default async function Home() {
  const data = await getDashboard();
  const dashboard = data.dashboard;

  return (
    <main className="min-h-screen bg-[#f4f1ec] text-zinc-900">
      <div className="mx-auto max-w-3xl px-4 py-5">
        <Header />
        <TodayCard today={dashboard} />
        <ScoreCard score={dashboard} />
        <GKReadyCard dashboard={dashboard} />
        <MissionCard missions={data.missions} />
        <AICoachCard ai={data.ai} />
        <DashboardAccordion dashboard={dashboard} ai={data.ai} />
        <PhilosophyCard philosophy={data.philosophy} />
      </div>
    </main>
  );
}
