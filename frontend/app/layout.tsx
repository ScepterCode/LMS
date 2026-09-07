import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { AuthProvider } from '@/contexts/AuthContext';
import { Toaster } from 'sonner';
import ConfirmHost from '@/components/ConfirmHost';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Learnlyf - Learning Management System',
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
        <AuthProvider>
          {children}
        </AuthProvider>
        <Toaster richColors closeButton position="top-right" />
        <ConfirmHost />
      </body>
    </html>
  );
}
