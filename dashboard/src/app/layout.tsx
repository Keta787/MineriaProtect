import type { Metadata } from "next";
import "./globals.css";
import { Navbar } from "@/components/Navbar";

export const metadata: Metadata = {
  title: "JobPath Observatory · Trayectorias Laborales y Métodos Numéricos (UNIMINUTO)",
  description:
    "Dashboard académico interactivo sobre el Censo Clasificado JobHop v2 (352,093 personas / 1,738,738 experiencias) enriquecido con la taxonomía europea ESCO v1.2.1 sobre Neon PostgreSQL.",
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
        <footer className="mt-12 border-t border-slate-200 bg-white py-6 text-xs text-slate-600">
          <div className="mx-auto flex max-w-7xl flex-col justify-between gap-4 px-4 sm:flex-row sm:items-center">
            <div>
              <p className="font-semibold text-slate-900">
                Proyecto Académico JobPath · Minería de Datos y Métodos Numéricos — UNIMINUTO Ibagué, Colombia
              </p>
              <p className="mt-0.5 text-slate-500">
                Datos fuente: <strong>JobHop v2</strong> (VDAB / Ghent University, <code>CC BY 4.0</code>) +{" "}
                <strong>Taxonomía ESCO v1.2.1</strong> (Comisión Europea, Decisión <code>2011/833/EU</code>,{" "}
                <code>CC BY 4.0</code>). Los identificadores <code>resume_id</code> provienen directamente del dataset público pseudonimizado.
              </p>
            </div>
            <div className="text-right font-mono text-[11px] text-slate-500">
              <div>Neon PostgreSQL 18 · Rol: jobpath_readonly</div>
              <div>268.60 MiB / 1,024 MiB (27.02% Plan Free) · LIMIT &le; 25</div>
            </div>
          </div>
        </footer>
      </body>
    </html>
  );
}
