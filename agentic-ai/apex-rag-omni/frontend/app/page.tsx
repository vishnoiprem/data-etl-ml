"use client";

import dynamic from "next/dynamic";

// Chat-style query UI. Lazy-loaded on the client because it uses
// browser-only state (localStorage, scroll position).
const Chat = dynamic(
  () => import("./components/Chat").then((m) => m.default),
  { ssr: false, loading: () => <p>loading chat…</p> },
);

export default function HomePage() {
  return <Chat />;
}