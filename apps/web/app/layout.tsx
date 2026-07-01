import type { Metadata } from "next";
import { ClerkProvider } from "@clerk/nextjs";
import { assertClerkEnv } from "../lib/clerk-env";
import { Providers } from "./providers";
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
  assertClerkEnv();

  return (
    <ClerkProvider>
      <html lang="en-IN">
        <body>
          <Providers>{children}</Providers>
        </body>
      </html>
    </ClerkProvider>
  );
}
