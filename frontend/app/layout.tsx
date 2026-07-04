import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { AuthProvider } from '@/contexts/AuthContext';
import { CookieCleaner } from './clear-cookies';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Nigerian LMS - Learning Management System',
  description: 'Modern learning management system for Nigerian schools',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <CookieCleaner />
        <AuthProvider>
          {children}
        </AuthProvider>
      </body>
    </html>
  );
}
