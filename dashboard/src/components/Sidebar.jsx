import React, { useRef } from "react";
import {
  LayoutDashboard,
  Network,
  FileWarning,
  GitPullRequest,
  Settings,
  TerminalSquare,
  GripVertical,
  CornerUpLeft,
} from "lucide-react";
import Logo from "./Logo.jsx";

export const NAV = [
  { id: "overview", label: "Overview", icon: LayoutDashboard },
  { id: "map", label: "Repository Map", icon: Network },
  { id: "staleness", label: "Staleness Report", icon: FileWarning },
  { id: "prs", label: "PR Activity", icon: GitPullRequest },
  { id: "console", label: "Live Console", icon: TerminalSquare },
  { id: "config", label: "Configuration", icon: Settings },
];

export default function Sidebar({ active, onChange, health, pos, setPos, docked }) {
  const drag = useRef(null);

  const onGripDown = (e) => {
    e.preventDefault();
    drag.current = { sx: e.clientX, sy: e.clientY, ox: pos.x, oy: pos.y };
    const onMove = (ev) => {
      if (!drag.current) return;
      const nx = drag.current.ox + (ev.clientX - drag.current.sx);
      const ny = drag.current.oy + (ev.clientY - drag.current.sy);
      // clamp so the panel can never be dragged fully off-screen
      const maxX = window.innerWidth - 120;
      const maxY = window.innerHeight - 120;
      setPos({ x: Math.max(-40, Math.min(nx, maxX)), y: Math.max(0, Math.min(ny, maxY)) });
    };
    const onUp = () => {
      drag.current = null;
      window.removeEventListener("pointermove", onMove);
      window.removeEventListener("pointerup", onUp);
    };
    window.addEventListener("pointermove", onMove);
    window.addEventListener("pointerup", onUp);
  };

  const dot =
    health === "red" ? "bg-clay" : health === "amber" ? "bg-sand" : "bg-sage";

  return (
    <aside
      className={`fixed left-0 top-0 z-40 flex w-64 flex-col border border-paper-50/[0.07] bg-ink-850/80 px-4 py-5 backdrop-blur-md transition-[box-shadow,border-radius,height] duration-300 ease-guide ${
        docked
          ? "h-screen border-y-0 border-l-0"
          : "max-h-[88vh] rounded-2xl shadow-card"
      }`}
      style={{ transform: `translate(${pos.x}px, ${pos.y}px)` }}
    >
      {/* drag handle */}
      <div className="mb-4 flex items-center justify-between">
        <div className="flex items-center gap-3 px-1">
          <Logo size={38} />
          <div>
            <p className="font-serif text-lg font-semibold leading-none tracking-tight text-paper-50">
              DocPilot
            </p>
            <p className="mt-1 text-[9px] font-semibold uppercase tracking-label text-paper-400">
              self-healing docs
            </p>
          </div>
        </div>
        <div className="flex items-center gap-1">
          {!docked && (
            <button
              onClick={() => setPos({ x: 0, y: 0 })}
              title="Dock to left"
              className="rounded-md p-1 text-paper-400 transition hover:bg-paper-50/10 hover:text-paper-50"
            >
              <CornerUpLeft size={14} />
            </button>
          )}
          <button
            onPointerDown={onGripDown}
            title="Drag to move the navigation"
            className="cursor-grab rounded-md p-1 text-paper-400 transition hover:bg-paper-50/10 hover:text-paper-50 active:cursor-grabbing"
          >
            <GripVertical size={16} />
          </button>
        </div>
      </div>

      <div className="rule mb-4 animate-rule-draw" />

      <nav className="flex flex-1 flex-col gap-1 overflow-y-auto" role="navigation">
        {NAV.map((item) => {
          const Icon = item.icon;
          const isActive = active === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onChange(item.id)}
              aria-current={isActive ? "page" : undefined}
              className={`nav-item ${isActive ? "nav-item-active" : ""}`}
            >
              <Icon size={16} strokeWidth={2} />
              {item.label}
            </button>
          );
        })}
      </nav>

      <div className="rule my-4" />

      <div className="flex items-center gap-2.5 px-1.5">
        <span className={`h-1.5 w-1.5 rounded-full ${dot} animate-breathe`} />
        <span className="text-[10px] font-semibold uppercase tracking-label text-paper-400">
          Engine connected
        </span>
      </div>
    </aside>
  );
}
