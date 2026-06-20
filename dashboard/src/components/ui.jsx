import React, { useEffect, useRef, useState } from "react";
import { CONFIDENCE, STATUS } from "../lib/format.js";

export function Skeleton({ className = "" }) {
  return <div className={`skeleton animate-shimmer rounded-md ${className}`} />;
}

// Animate a number from 0 up to `target` once it becomes available.
function useCountUp(target, duration = 900) {
  const [value, setValue] = useState(0);
  const raf = useRef();
  useEffect(() => {
    const end = Number(target);
    if (!Number.isFinite(end)) return;
    const start = performance.now();
    const tick = (now) => {
      const p = Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(1 - p, 3); // ease-out cubic
      setValue(Math.round(eased * end));
      if (p < 1) raf.current = requestAnimationFrame(tick);
    };
    raf.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf.current);
  }, [target, duration]);
  return value;
}

export function ConfidenceBadge({ value }) {
  const c = CONFIDENCE[value] || CONFIDENCE.low;
  return <span className={`chip ${c.cls}`}>{c.label}</span>;
}

export function StatusBadge({ value }) {
  const s = STATUS[value] || STATUS.pending;
  return <span className={`chip ${s.cls}`}>{s.label}</span>;
}

export function StatCard({ icon: Icon, label, value, accent = "clay", loading }) {
  const tone = accent === "cyan" ? "text-sand" : "text-clay";
  const isNumeric = Number.isFinite(Number(value));
  const counted = useCountUp(isNumeric ? Number(value) : 0);
  return (
    <div className="glass glass-hover animate-slide-in p-5 transition-transform duration-300 ease-guide hover:-translate-y-0.5">
      <div className="flex items-start justify-between">
        <span className="text-[10px] font-semibold uppercase tracking-label text-paper-400">
          {label}
        </span>
        <span className={`border border-paper-50/10 rounded-md p-2 ${tone}`}>
          {Icon && <Icon size={16} strokeWidth={2} />}
        </span>
      </div>
      {loading ? (
        <Skeleton className="mt-4 h-10 w-20" />
      ) : (
        <div className="mt-3 font-serif text-5xl font-semibold tracking-tight text-paper-50">
          {isNumeric ? counted : value}
        </div>
      )}
    </div>
  );
}

export function SectionHeader({ title, subtitle, children }) {
  return (
    <div className="mb-7">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="font-serif text-3xl font-semibold tracking-tight text-paper-50">
            {title}
          </h1>
          {subtitle && <p className="mt-1.5 max-w-xl text-sm text-paper-400">{subtitle}</p>}
        </div>
        {children}
      </div>
      <div className="rule mt-5 animate-rule-draw" />
    </div>
  );
}

export function EmptyState({ icon: Icon, title, hint }) {
  return (
    <div className="glass flex flex-col items-center justify-center gap-3 px-6 py-16 text-center">
      {Icon && <Icon size={28} className="text-paper-400" strokeWidth={1.5} />}
      <p className="font-serif text-lg text-paper-100">{title}</p>
      {hint && <p className="max-w-sm text-xs text-paper-400">{hint}</p>}
    </div>
  );
}
