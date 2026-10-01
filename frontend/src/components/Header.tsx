"use client";

import React from "react";
import { GraduationCap, ShieldCheck, Sparkles, BookOpen } from "lucide-react";

export function Header() {
  return (
    <header className="sticky top-0 z-40 w-full border-b border-slate-200/80 bg-white/95 backdrop-blur-md">
      <div className="container mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-tr from-emerald-600 to-emerald-500 text-white shadow-md shadow-emerald-500/20">
            <GraduationCap className="h-6 w-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xl font-bold tracking-tight text-slate-900">
                Ethio<span className="text-emerald-600">Format</span>
              </span>
              <span className="rounded-full bg-emerald-50 px-2 py-0.5 text-[11px] font-semibold text-emerald-700 border border-emerald-200">
                ኢትዮ-ፎርማት v1.0
              </span>
            </div>
            <p className="text-[11px] text-slate-500">Automated Ethiopian Thesis & Dissertation Formatter</p>
          </div>
        </div>

        <div className="hidden md:flex items-center gap-6 text-sm font-medium text-slate-600">
          <div className="flex items-center gap-1.5 text-xs text-slate-500">
            <ShieldCheck className="h-4 w-4 text-emerald-600" />
            <span>22 Ethiopian Universities Standard</span>
          </div>
          <div className="flex items-center gap-1.5 text-xs text-slate-500">
            <Sparkles className="h-4 w-4 text-amber-500" />
            <span>Free 3-Page Instant Preview</span>
          </div>
        </div>
      </div>
    </header>
  );
}
