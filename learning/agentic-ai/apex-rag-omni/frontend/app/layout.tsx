import "./globals.css";

export const metadata = {
  title: "apex-rag-omni",
  description: "grounded RAG over your knowledge base",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}