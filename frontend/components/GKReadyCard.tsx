import Badge from "@/components/ui/Badge";

type Props = {
  dashboard: any;
};

const descriptions: Record<string, string> = {
  ELITE: "최상의 컨디션입니다.",
  READY: "오늘은 계획한 운동을 진행하기 좋은 상태입니다.",
  NORMAL: "평소와 비슷한 컨디션입니다.",
  CARE: "무리하지 말고 컨디션을 확인하세요.",
  RECOVERY: "회복을 우선하는 하루를 추천합니다.",
};

export default function GKReadyCard({ dashboard }: Props) {
  const level = dashboard.gk_readiness_level ?? "NORMAL";

  return (
    <section className="mt-5 rounded-2xl border border-[#ddd6ce] bg-white p-5 shadow-sm">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-black">
          GK READY
        </h2>

        <Badge label={level} />
      </div>

      <p className="mt-4 text-zinc-600">
        {descriptions[level]}
      </p>
    </section>
  );
}
