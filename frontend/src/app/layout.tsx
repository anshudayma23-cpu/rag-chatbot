import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'FundBot | HDFC Mutual Fund Assistant',
  description: 'AI-powered factual assistant for HDFC Mutual Funds',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}
