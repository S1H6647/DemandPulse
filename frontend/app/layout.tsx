import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "DemandPulse · Daily demand forecasting",
  description:
    "Explore daily store demand with calendar-aware sales forecasts.",
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
