import { useState } from "react";

export function ThemeToggle() {
  const [dark, setDark] = useState(() => document.documentElement.classList.contains("dark"));

  const toggle = () => {
    const next = !dark;
    document.documentElement.classList.toggle("dark", next);
    try {
      localStorage.setItem("theme", next ? "dark" : "light");
    } catch {
      // storage blocked: the choice simply lasts for this visit
    }
    setDark(next);
  };

  return (
    <button
      onClick={toggle}
      className="block w-full rounded-md px-3 py-2 text-left text-sm hover:bg-white/5"
    >
      {dark ? "Light mode" : "Dark mode"}
    </button>
  );
}
