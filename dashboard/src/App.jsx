import React, { useEffect, useState } from "react";
import Sidebar, { NAV } from "./components/Sidebar.jsx";
import SplashScreen from "./components/SplashScreen.jsx";
import CustomCursor from "./components/CustomCursor.jsx";
import { ToastProvider } from "./hooks/useToast.jsx";
import { api, SAMPLE, withFallback } from "./api/client.js";
import Overview from "./pages/Overview.jsx";
import RepositoryMap from "./pages/RepositoryMap.jsx";
import StalenessReport from "./pages/StalenessReport.jsx";
import PRActivity from "./pages/PRActivity.jsx";
import LiveConsole from "./pages/LiveConsole.jsx";
import Configuration from "./pages/Configuration.jsx";

const PAGES = {
  overview: Overview,
  map: RepositoryMap,
  staleness: StalenessReport,
  prs: PRActivity,
  console: LiveConsole,
  config: Configuration,
};

function loadNavPos() {
  try {
    return JSON.parse(localStorage.getItem("docpilot-nav-pos")) || { x: 0, y: 0 };
  } catch {
    return { x: 0, y: 0 };
  }
}

export default function App() {
  const [booting, setBooting] = useState(true);
  const [active, setActive] = useState("overview");
  const [health, setHealth] = useState("green");
  const [navPos, setNavPos] = useState(loadNavPos);

  const docked = navPos.x === 0 && navPos.y === 0;

  useEffect(() => {
    withFallback(api.overview, SAMPLE.overview).then((d) => setHealth(d.health));
  }, []);

  useEffect(() => {
    localStorage.setItem("docpilot-nav-pos", JSON.stringify(navPos));
  }, [navPos]);

  // Keyboard navigation: Alt+1..6 jump between sections.
  useEffect(() => {
    const onKey = (e) => {
      if (e.altKey && e.key >= "1" && e.key <= String(NAV.length)) {
        setActive(NAV[Number(e.key) - 1].id);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const Page = PAGES[active];
  const index = NAV.findIndex((n) => n.id === active);

  return (
    <ToastProvider>
      <CustomCursor />
      {booting && <SplashScreen onDone={() => setBooting(false)} />}

      <div className="h-screen overflow-hidden">
        <Sidebar
          active={active}
          onChange={setActive}
          health={health}
          pos={navPos}
          setPos={setNavPos}
          docked={docked}
        />
        <main
          className="h-screen overflow-y-auto px-6 py-9 transition-[margin] duration-300 ease-guide md:px-12"
          style={{ marginLeft: docked ? "16rem" : "0" }}
        >
          <div className="mx-auto max-w-6xl">
            <div key={active} className="animate-page-in">
              <div className="mb-5 flex items-center gap-3 text-[10px] font-semibold uppercase tracking-label text-paper-400">
                <span className="font-mono text-clay">{String(index + 1).padStart(2, "0")}</span>
                <span className="h-px w-8 bg-paper-50/20" />
                <span>DocPilot Control</span>
              </div>
              <Page />
            </div>
          </div>
        </main>
      </div>
    </ToastProvider>
  );
}
