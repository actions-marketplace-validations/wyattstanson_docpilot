import React, { useEffect, useRef, useState } from "react";

// A custom pointer: an instant clay dot + a trailing ring that lags behind and
// grows over interactive elements. Disabled on touch / coarse pointers and when
// the user prefers reduced motion (native cursor is kept in those cases).
export default function CustomCursor() {
  const dotRef = useRef(null);
  const ringRef = useRef(null);
  const [enabled] = useState(() => {
    if (typeof window === "undefined") return false;
    return (
      !window.matchMedia("(pointer: coarse)").matches &&
      !window.matchMedia("(prefers-reduced-motion: reduce)").matches
    );
  });

  useEffect(() => {
    if (!enabled) return;
    const dot = dotRef.current;
    const ring = ringRef.current;
    if (!dot || !ring) return;
    document.body.classList.add("custom-cursor");
    let mx = window.innerWidth / 2;
    let my = window.innerHeight / 2;
    let rx = mx;
    let ry = my;
    let raf;

    const onMove = (e) => {
      mx = e.clientX;
      my = e.clientY;
      dot.style.transform = `translate(${mx}px, ${my}px)`;
    };
    const onDown = () => ring.classList.add("cursor-down");
    const onUp = () => ring.classList.remove("cursor-down");
    const onOver = (e) => {
      const interactive = e.target.closest("a, button, input, textarea, select, label, [role=button]");
      ring.classList.toggle("cursor-hover", !!interactive);
    };
    const onLeave = () => {
      dot.style.opacity = "0";
      ring.style.opacity = "0";
    };
    const onEnter = () => {
      dot.style.opacity = "1";
      ring.style.opacity = "1";
    };

    const loop = () => {
      // lerp the ring toward the cursor for a smooth trailing feel
      rx += (mx - rx) * 0.18;
      ry += (my - ry) * 0.18;
      ring.style.transform = `translate(${rx}px, ${ry}px)`;
      raf = requestAnimationFrame(loop);
    };
    loop();

    window.addEventListener("mousemove", onMove);
    window.addEventListener("mousedown", onDown);
    window.addEventListener("mouseup", onUp);
    window.addEventListener("mouseover", onOver);
    document.addEventListener("mouseleave", onLeave);
    document.addEventListener("mouseenter", onEnter);
    return () => {
      cancelAnimationFrame(raf);
      document.body.classList.remove("custom-cursor");
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("mousedown", onDown);
      window.removeEventListener("mouseup", onUp);
      window.removeEventListener("mouseover", onOver);
      document.removeEventListener("mouseleave", onLeave);
      document.removeEventListener("mouseenter", onEnter);
    };
  }, []);

  if (!enabled) return null;
  return (
    <>
      <div ref={ringRef} className="cursor-ring" aria-hidden="true" />
      <div ref={dotRef} className="cursor-dot" aria-hidden="true" />
    </>
  );
}
