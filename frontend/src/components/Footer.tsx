"use client";

import React from "react";
import { GraduationCap, ShieldCheck } from "lucide-react";

export function Footer() {
  return (
    <footer className="w-full border-t border-slate-200/80 dark:border-slate-800/80 bg-white dark:bg-slate-950 py-8 text-xs text-slate-500 dark:text-slate-400 transition-colors duration-200">
      <div className="container mx-auto max-w-6xl px-4 sm:px-6 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <div className="flex h-6 w-6 items-center justify-center rounded-lg bg-emerald-600 text-white">
            <GraduationCap className="h-4 w-4" />
          </div>
          <span className="font-semibold text-slate-800 dark:text-slate-200">EthioFormat © 2026</span>
          <span>•</span>
          <span>Ethiopian Academic Thesis Automation</span>
        </div>

        <div className="flex items-center gap-6 text-slate-500 dark:text-slate-400">
          <div className="flex items-center gap-1">
            <ShieldCheck className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
            <span>Strict SGS Standards</span>
          </div>
          <span>•</span>
          <span>All 22 Public Universities</span>
        </div>
      </div>
    </footer>
  );
}
