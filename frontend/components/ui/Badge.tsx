interface BadgeProps {
  label: string;
}

const styles: Record<
  string,
  {
    bg: string;
    text: string;
    icon: string;
  }
> = {
  ELITE: { bg: "bg-blue-100", text: "text-blue-700", icon: "🔵" },
  READY: { bg: "bg-green-100", text: "text-green-700", icon: "🟢" },
  GREEN: { bg: "bg-green-100", text: "text-green-700", icon: "🟢" },
  NORMAL: { bg: "bg-yellow-100", text: "text-yellow-700", icon: "🟡" },
  YELLOW: { bg: "bg-yellow-100", text: "text-yellow-700", icon: "🟡" },
  CARE: { bg: "bg-orange-100", text: "text-orange-700", icon: "🟠" },
  RECOVERY: { bg: "bg-red-100", text: "text-red-700", icon: "🔴" },
  RED: { bg: "bg-red-100", text: "text-red-700", icon: "🔴" },
};

export default function Badge({ label }: BadgeProps) {
  const item = styles[label] ?? {
    bg: "bg-gray-100",
    text: "text-gray-700",
    icon: "⚪",
  };

  return (
    <span
      className={[
        "inline-flex items-center gap-2 rounded-full px-4 py-1.5 text-sm font-bold",
        item.bg,
        item.text,
      ].join(" ")}
    >
      <span>{item.icon}</span>
      {label}
    </span>
  );
}
