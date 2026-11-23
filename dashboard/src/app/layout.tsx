import type { Metadata } from "next";
import "./globals.css";
import { Navbar } from "@/components/Navbar";

export const metadata: Metadata = {
  title: "JobPath Explorer · Demo Interactivo de Datos (JobHop v2 + ESCO v1.2.1)",
  description:
    "Explorador interactivo de trayectorias laborales conectado en modo de solo lectura a Neon PostgreSQL (JobHop v2 + catálogo ESCO v1.2.1).",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es">
      <body className="min-h-screen flex flex-col bg-slate-50 text-slate-900">
        <Navbar />
        <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-6 sm:px-6">
          {children}
        </main>
        <footer className="mt-12 border-t border-slate-200 bg-white py-5 text-xs text-slate-600">
          <div className="mx-auto flex max-w-7xl flex-col justify-between gap-3 px-4 sm:flex-row sm:items-center">
            <div>
              <p className="font-semibold text-slate-900">
                JobPath Explorer · Demo interactivo de datos (UNIMINUTO Ibagué)
              </p>
              <p className="mt-0.5 text-slate-500">
                Fuentes públicas: <strong>JobHop v2</strong> (VDAB / Ghent University) +{" "}
                <strong>ESCO v1.2.1</strong> (Comisión Europea). Los identificadores{" "}
                <code>resume_id</code> provienen del dataset público pseudonimizado.
              </p>
            </div>
            <div className="text-right font-mono text-[11px] text-slate-500">
              <div>Neon PostgreSQL 18 · Solo lectura (Server-Only)</div>
              <div>Despliegue Preview · Paginado sin descarga masiva</div>
            </div>
          </div>
        </footer>
      </body>
    </html>
  );
}
