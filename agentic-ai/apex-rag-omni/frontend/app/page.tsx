"use client";

import dynamic from "next/dynamic";

// Virtualized trace reviewer. Lazy-loaded on the client because
// react-window touches window/DOM APIs that don't exist on the server.
const ApexRagOmni = dynamic(
  () => import("./components/ApexRagOmni").then((m) => m.default),
  { ssr: false, loading: () => <p>loading trace reviewer…</p> },
);

export default function HomePage() {
  return <ApexRagOmni />;
}
