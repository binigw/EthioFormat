"use client";

import React from "react";
import { formatETB } from "@/lib/utils";
import { PricingDetail } from "@/types";
import { Lock, Sparkles, ShieldCheck, ArrowRight, Layers, FileCheck } from "lucide-react";

interface BlurPaywallHookProps {
  totalPages: number;
  pricing: PricingDetail;
  onPayClick: () => void;
  disabled?: boolean;
}

export function BlurPaywallHook({
  totalPages,
  pricing,
  onPayClick,
  disabled = false,
}: BlurPaywallHookProps) {
  const lockedPagesCount = Math.max(0, totalPages - 3);

  return (
    <div className="relative mt-8 rounded-2xl border-2 border-emerald-500/40 bg-gradient-to-b from-slate-900/90 to-slate-950 text-white p-6 sm:p-8 overflow-hidden shadow-2xl">
      {/* Background Decorative Grid */}
      <div className="absolute inset-0 bg-[radial-gradient(#10b981_1px,transparent_1px)] [background-size:16px_16px] opacity-15" />
      
      {/* Stacked Faded Page Wireframes Visualizing Remaining Locked Pages */}
      <div className="relative z-10 max-w-xl mx-auto text-center space-y-5">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/20 border border-emerald-500/40 text-emerald-300 text-xs font-semibold backdrop-blur-md">
          <Lock className="h-3.5 w-3.5 text-emerald-400" />
          <span>Paywall Protected Preview • {lockedPagesCount} Pages Locked</span>
        </div>

        <div className="space-y-2">
          <h3 className="text-xl sm:text-2xl font-extrabold tracking-tight text-white">
            Unlock & Download Full Formatted Thesis
          </h3>
          <p className="text-sm text-slate-300">
            Pages 1, 2, and 3 are previewed above. Your complete document contains{" "}
            <span className="font-bold text-emerald-400">{totalPages} pages</span> formatted strictly according to institutional standards.
          </p>
        </div>

        {/* Dynamic Pricing Breakdown Card */}
        <div className="p-4 rounded-xl bg-white/10 border border-white/15 backdrop-blur-md text-left text-xs sm:text-sm space-y-2">
          <div className="flex justify-between items-center text-slate-300">
            <span>Base Formatting Fee (Up to 20 Pages):</span>
            <span className="font-semibold text-white">{formatETB(pricing.base_fee)}</span>
          </div>
          {pricing.incremental_fee > 0 && (
            <div className="flex justify-between items-center text-slate-300">
              <span>Extended Document Fee ({totalPages - 20} pages × 1.50 ETB):</span>
              <span className="font-semibold text-white">+{formatETB(pricing.incremental_fee)}</span>
            </div>
          )}
          <div className="border-t border-white/20 pt-2 flex justify-between items-center text-sm sm:text-base font-bold text-emerald-400">
            <span>Total Formatting Fee:</span>
            <span className="text-lg text-emerald-300">{formatETB(pricing.total_fee)}</span>
          </div>
        </div>

        {/* CTA Button */}
        <div className="pt-2 space-y-3">
          <button
            type="button"
            disabled={disabled}
            onClick={onPayClick}
            className="w-full sm:w-auto inline-flex items-center justify-center gap-3 px-8 py-4 rounded-xl bg-gradient-to-r from-emerald-500 via-emerald-600 to-teal-600 text-white font-bold text-base shadow-lg shadow-emerald-500/30 hover:shadow-emerald-500/50 hover:scale-[1.02] active:scale-[0.98] transition-all disabled:opacity-60 disabled:cursor-not-allowed cursor-pointer"
          >
            <span>Pay {formatETB(pricing.total_fee)} via Chapa / Telebirr</span>
            <ArrowRight className="h-5 w-5" />
          </button>

          <div className="flex flex-wrap items-center justify-center gap-4 text-[11px] text-slate-400 pt-2">
            <span className="flex items-center gap-1">
              <ShieldCheck className="h-3.5 w-3.5 text-emerald-400" /> Instant Chapa Verification
            </span>
            <span>•</span>
            <span className="flex items-center gap-1">
              <FileCheck className="h-3.5 w-3.5 text-emerald-400" /> Full .DOCX Delivery
            </span>
            <span>•</span>
            <span className="flex items-center gap-1">
              <Layers className="h-3.5 w-3.5 text-emerald-400" /> 24h Secure Access Link
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
