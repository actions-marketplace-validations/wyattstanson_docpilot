import React, { useEffect, useState } from "react";
import Logo from "./Logo.jsx";

const MESSAGES = [
  "Parsing code + docs…",
  "Building the link graph…",
  "Checking for staleness…",
  "Ready.",
];

// A one-time welcome / loading overlay. Animates the compass in, fills a
// progress rule, cycles loading messages, then fades out and calls onDone.
export default function SplashScreen({ onDone }) {
  const [progress, setProgress] = useState(0);
  const [msg, setMsg] = useState(0);
  const [leaving, setLeaving] = useState(false);

  useEffect(() => {
    const total = 2100;
    // Cosmetic progress bar via rAF (pauses if the tab is backgrounded — fine).
    const start = performance.now();
    let raf;
    const tick = (now) => {
      const p = Math.min(1, (now - start) / total);
      setProgress(p);
      if (p < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);

    // Message cycling + guaranteed completion via setTimeout (fires even when
    // backgrounded, so the splash can never hang and block the app).
    const msgTimers = MESSAGES.map((_, i) =>
      setTimeout(() => setMsg(i), (i / MESSAGES.length) * total),
    );
    const leaveT = setTimeout(() => setLeaving(true), total);
    const doneT = setTimeout(onDone, total + 650);

    return () => {
      cancelAnimationFrame(raf);
      msgTimers.forEach(clearTimeout);
      clearTimeout(leaveT);
      clearTimeout(doneT);
    };
  }, [onDone]);

  return (
    <div
      className={`fixed inset-0 z-[100] grid place-items-center bg-ink-900 transition-opacity duration-700 ease-guide ${
        leaving ? "opacity-0 pointer-events-none" : "opacity-100"
      }`}
      style={{
        backgroundImage:
          "radial-gradient(120% 80% at 50% 30%, rgba(217,84,47,0.10), transparent 60%)",
      }}
    >
      <div className="flex flex-col items-center gap-6 px-6 text-center">
        <div className="splash-logo">
          <Logo size={88} />
        </div>

        <div className="space-y-2">
          <h1 className="splash-title font-serif text-4xl font-semibold tracking-tight text-paper-50">
            Welcome to DocPilot
          </h1>
          <p className="splash-sub text-[11px] font-semibold uppercase tracking-label text-paper-400">
            self-healing technical documentation
          </p>
        </div>

        <div className="splash-bar mt-2 h-px w-64 overflow-hidden bg-paper-50/10">
          <div
            className="h-full bg-clay transition-[width] duration-100 ease-out"
            style={{ width: `${progress * 100}%` }}
          />
        </div>

        <p className="h-4 font-mono text-xs text-paper-400">{MESSAGES[msg]}</p>
      </div>
    </div>
  );
}
