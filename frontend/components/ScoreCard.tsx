import Badge from "@/components/ui/Badge";
import Card from "@/components/ui/Card";

type Score = {
  grade?: string;
};

export default function ScoreCard({ score }: { score: Score }) {
  const grade = score.grade ?? "GREEN";

  return (
    <Card>
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-sm font-bold text-zinc-500">오늘의 흐름</p>
          <p className="mt-2 text-xl font-black text-zinc-900">
            오늘도 Journey는 이어졌습니다.
          </p>
        </div>

        <Badge label={grade} />
      </div>
    </Card>
  );
}
