import MedicationCard from "@/components/MedicationCard";
import WorkoutCard from "@/components/WorkoutCard";
import MealCard from "@/components/MealCard";

type Props = {
  dashboard: any;
  ai: any;
};

export default function DashboardAccordion({ dashboard, ai }: Props) {
  return (
    <section className="mt-5 rounded-2xl border border-[#ddd6ce] bg-white shadow-sm">
      <details className="group">
        <summary className="flex cursor-pointer list-none items-center justify-between p-5">
          <div>
            <p className="text-sm font-bold text-zinc-500">오늘 기록</p>
            <h2 className="mt-1 text-xl font-black">운동 · 식단 · 약 체크 보기</h2>
          </div>

          <span className="text-2xl transition-transform group-open:rotate-180">
            ⌄
          </span>
        </summary>

        <div className="border-t border-[#eee6dc] px-5 pb-5">
          <MedicationCard today={dashboard} />
          <WorkoutCard today={dashboard} ai={ai} />
          <MealCard today={dashboard} ai={ai} />
        </div>
      </details>
    </section>
  );
}
