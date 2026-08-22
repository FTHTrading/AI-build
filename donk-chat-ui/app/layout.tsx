import React from "react";
import "./globals.css";

export const metadata = {
  title: "Donk Interactive Runtime | Unykorn LLC",
  description: "Candid AI Execution & EIP-712 Structured Data Engine",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-[#090b0e] text-zinc-100 font-sans antialiased">
        {children}
      </body>
    </html>
  );
}
