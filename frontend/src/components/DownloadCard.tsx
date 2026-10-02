"use client";

import React, { useState, useEffect } from "react";
import { PaymentVerificationResponse } from "@/types";
import { Download, CheckCircle2, ShieldCheck, Clock, FileCheck, ArrowLeft } from "lucide-react";

interface DownloadCardProps {
  paymentData: PaymentVerificationResponse;
  fileName: string;
  onReset: () => void;
}

export function DownloadCard({ paymentData, fileName, onReset }: DownloadCardProps) {
  const [timeLeft, setTimeLeft] = useState(24 * 3600); // 24 hours in seconds

  useEffect(() => {
    const timer = setInterval(() => {
      setTimeLeft((prev) => (prev > 0 ? prev - 1 : 0));
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const formatHours = (seconds: number) => {
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    return `${hrs.toString().padStart(2, "0")}:${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
  };

  // Ensure download URL is properly resolved:
  // 1. Supabase 24h signed URL (starts with http/https) -> used directly
  // 2. Relative API link (/api/download/...) -> prepended with live backend base URL
  const backendBase = (process.env.NEXT_PUBLIC_API_URL || "https://ethioformat.onrender.com/api").replace(/\/api\/?$/, "");
  let downloadUrl = paymentData.download_url || "#";
  if (downloadUrl.startsWith("/api/download/")) {
    downloadUrl = `${backendBase}${downloadUrl}`;
  }

  return (
    <div className="w-full max-w-2xl mx-auto bg-white rounded-3xl border border-emerald-200 shadow-2xl overflow-hidden animate-in fade-in-50 zoom-in-95 duration-300">
      <div className="bg-gradient-to-r from-emerald-600 to-teal-700 px-6 py-8 text-white text-center space-y-2">
        <div className="inline-flex p-3 rounded-full bg-white/20 backdrop-blur-md mb-2 shadow-inner">
          <CheckCircle2 className="h-10 w-10 text-emerald-200" />
        </div>
        <h2 className="text-2xl font-black tracking-tight">Payment Verified & Complete!</h2>
        <p className="text-sm text-emerald-100 max-w-md mx-auto">
          Your thesis has been fully formatted and compiled according to your university guidelines.
        </p>
      </div>

      <div className="p-6 sm:p-8 space-y-6">
        {/* Document Info Card */}
        <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 flex items-center justify-between">
          <div className="flex items-center gap-3 overflow-hidden">
            <div className="w-12 h-12 rounded-xl bg-emerald-100 text-emerald-700 flex items-center justify-center flex-shrink-0">
              <FileCheck className="h-6 w-6" />
            </div>
            <div className="truncate">
              <div className="font-bold text-slate-900 truncate">{paymentData.file_name || fileName}</div>
              <div className="text-xs text-slate-500">Microsoft Word OpenXML (.docx)</div>
            </div>
          </div>
          <span className="px-2.5 py-1 rounded-full bg-emerald-100 text-emerald-800 text-xs font-semibold">
            Unlocked
          </span>
        </div>

        {/* Expiration Timer Card */}
        <div className="flex items-center justify-between p-3.5 rounded-xl bg-amber-50/80 border border-amber-200 text-xs text-amber-900">
          <div className="flex items-center gap-2">
            <Clock className="h-4 w-4 text-amber-700 flex-shrink-0" />
            <span>Secure Download Link Active for:</span>
          </div>
          <span className="font-mono font-bold text-amber-950 text-sm">{formatHours(timeLeft)}</span>
        </div>

        {/* Primary Download CTA */}
        <div className="space-y-3">
          <a
            href={downloadUrl}
            target="_blank"
            rel="noopener noreferrer"
            download={paymentData.file_name || fileName}
            className="w-full inline-flex items-center justify-center gap-3 py-4 px-6 rounded-2xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 text-white font-extrabold text-base shadow-xl shadow-emerald-600/30 hover:shadow-emerald-600/50 hover:scale-[1.01] active:scale-[0.99] transition-all text-center cursor-pointer"
          >
            <Download className="h-5 w-5" />
            <span>Download Formatted Thesis (.docx)</span>
          </a>

          <button
            type="button"
            onClick={onReset}
            className="w-full inline-flex items-center justify-center gap-2 py-3 px-4 rounded-xl text-slate-600 hover:text-slate-900 hover:bg-slate-100 text-sm font-semibold transition-colors cursor-pointer"
          >
            <ArrowLeft className="h-4 w-4" />
            <span>Format Another Thesis</span>
          </button>
        </div>

        <div className="pt-2 border-t border-slate-100 text-center text-xs text-slate-400 flex items-center justify-center gap-1.5">
          <ShieldCheck className="h-4 w-4 text-emerald-600" />
          <span>Verified Ethiopian Academic Standard • 100% Guaranteed Layout Compliance</span>
        </div>
      </div>
    </div>
  );
}
