import type { Metadata } from "next";
import "@fontsource-variable/archivo";
import "@fontsource-variable/fraunces";
import "./globals.css";
import { AppHeader } from "@/components/AppHeader";

export const metadata: Metadata = {
  title: { default: "Display Check | KKG", template: "%s | Display Check" },
  description: "A workspace for retail display planning, by KKG.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <a className="skip-link" href="#main">Skip to content</a>
        <AppHeader />
        {children}
        <footer className="site-footer"><span>Display Check <span className="muted">/ A KKG product</span></span><span>Built around the display.</span></footer>
      </body>
    </html>
  );
}
