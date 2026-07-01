import Card from "@/components/ui/Card";

type Today = {
  day_no?: number;
  week_no?: number;
  record_date?: string;
};

export default function TodayCard({ today }: { today: Today }) {
  return (
    <Card>
      <div className="grid grid-cols-3 gap-3 text-center">
        <Info label="DAY" value={String(today.day_no ?? "-")} />
        <Info label="WEEK" value={String(today.week_no ?? "-")} />
        <Info label="DATE" value={today.record_date ?? "-"} />
      </div>
    </Card>
  );
}

function Info({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs font-black text-zinc-400">{label}</p>
      <p className="mt-1 text-lg font-black text-zinc-900">{value}</p>
    </div>
  );
}
