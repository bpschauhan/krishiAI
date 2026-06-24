import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "KrishiAI",
  description: "Agricultural operating system for farmers in Uttar Pradesh, India."
};

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en-IN">
      <body>{children}</body>
    </html>
  );
}
