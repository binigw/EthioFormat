"use client";

import React from "react";
import { GraduationCap, ShieldCheck, Sparkles } from "lucide-react";

export function Header() {
  return (
    <header className="sticky top-0 z-40 w-full border-b border-slate-800/80 bg-slate-950/90 backdrop-blur-md">
      <div className="container mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-tr from-emerald-600 to-emerald-500 text-white shadow-md shadow-emerald-500/20 flex-shrink-0">
            <GraduationCap className="h-6 w-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xl font-bold tracking-tight text-white">
                Ethio<span className="text-emerald-400">Format</span>
              </span>
              <span className="rounded-full bg-emerald-950/60 px-2 py-0.5 text-[11px] font-semibold text-emerald-300 border border-emerald-800">
                ኢትዮ-ፎርማት
              </span>
            </div>
            <p className="text-[11px] text-slate-400">Automated Ethiopian Thesis Formatter</p>
          </div>
        </div>

        <div className="flex items-center gap-6 text-sm font-medium">
          <div className="flex items-center gap-1.5 text-xs text-slate-400">
            <ShieldCheck className="h-4 w-4 text-emerald-400" />
            <span>22 Universities Standard</span>
          </div>
          <div className="hidden sm:flex items-center gap-1.5 text-xs text-slate-400">
            <Sparkles className="h-4 w-4 text-amber-400" />
            <span>Free 3-Page Preview</span>
          </div>
        </div>
      </div>
    </header>
  );
}
