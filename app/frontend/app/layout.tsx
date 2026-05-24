export const metadata = {
  title: "Voice Studio",
  description: "Local XTTS + RVC voice engine",
};

import "./globals.css";

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
