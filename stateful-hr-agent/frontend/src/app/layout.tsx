import './globals.css'

export const metadata = {
  title: 'Stateful HR Agent — AI-Generated Workspace',
  description: 'An agentic HR platform powered by LangGraph + AG-UI. The AI dynamically creates and manages your HR workspace.',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet" />
      </head>
      <body className="overflow-hidden">{children}</body>
    </html>
  )
}
