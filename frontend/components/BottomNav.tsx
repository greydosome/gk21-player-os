"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const navItems = [
  { href: "/", label: "Home", icon: "🏠" },
  { href: "/record", label: "Record", icon: "📝" },
  { href: "/weekly", label: "Weekly", icon: "📈" },
  { href: "/history", label: "History", icon: "📚" },
  { href: "/settings", label: "More", icon: "⚙️" },
];

export default function BottomNav() {
  const pathname = usePathname();

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-50 border-t border-[#ddd6ce] bg-white/95 px-2 py-2 backdrop-blur">
      <div className="mx-auto grid max-w-3xl grid-cols-5 gap-1">
        {navItems.map((item) => {
          const active =
            item.href === "/"
              ? pathname === "/"
              : pathname.startsWith(item.href);

          return (
            <Link
              key={item.href}
              href={item.href}
              className={[
                "flex flex-col items-center justify-center rounded-2xl px-2 py-2 text-xs font-black transition",
                active
                  ? "bg-slate-900 text-white"
                  : "text-zinc-500 active:bg-[#f4f1ec]",
              ].join(" ")}
            >
              <span className="text-xl">{item.icon}</span>
              <span className="mt-1">{item.label}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
