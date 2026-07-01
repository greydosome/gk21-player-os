import Header from "@/components/Header";
import TodayCard from "@/components/TodayCard";
import ScoreCard from "@/components/ScoreCard";
import AICoachCard from "@/components/AICoachCard";
import MissionCard from "@/components/MissionCard";
import GKReadyCard from "@/components/GKReadyCard";
import MedicationCard from "@/components/MedicationCard";
import WorkoutCard from "@/components/WorkoutCard";
import MealCard from "@/components/MealCard";

async function getDashboard() {
  const res = await fetch(
    "http://127.0.0.1:8000/api/dashboard?record_date=2026-06-29",
    {
      cache: "no-store",
    }
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
    <main className="min-h-screen bg-[#f4f1ec]">
      <div className="mx-auto max-w-6xl px-4 py-6">

        <Header />

        <TodayCard today={dashboard} />

        <ScoreCard score={dashboard} />

        <AICoachCard ai={data.ai} />

        <MissionCard missions={data.missions} />

        <GKReadyCard dashboard={dashboard} />

        <MedicationCard today={dashboard} />

        <WorkoutCard
          today={dashboard}
          ai={data.ai}
        />

        <MealCard
          today={dashboard}
          ai={data.ai}
        />

      </div>
    </main>
  );
}
