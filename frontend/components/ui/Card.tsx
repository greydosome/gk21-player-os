import { ReactNode } from "react";

interface Props {
  title?: string;
  children: ReactNode;
  className?: string;
}

export default function Card({
  title,
  children,
  className = "",
}: Props) {
  return (
    <section
      className={`rounded-2xl border border-[#ddd6ce] bg-white p-5 shadow-sm ${className}`}
    >
      {title && (
        <h2 className="mb-4 text-lg font-black text-zinc-900">
          {title}
        </h2>
      )}

      {children}
    </section>
  );
}
