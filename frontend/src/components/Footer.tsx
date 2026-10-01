"use client";

import React from "react";
import { GraduationCap, ShieldCheck, Heart } from "lucide-react";

export function Footer() {
  return (
    <footer className="w-full border-t border-slate-200 bg-white py-12 text-slate-600 mt-auto">
      <div className="container mx-auto max-w-6xl px-4 sm:px-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
          <div className="md:col-span-2 space-y-3">
            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-600 text-white font-bold">
                <GraduationCap className="h-5 w-5" />
              </div>
              <span className="text-lg font-bold text-slate-900">EthioFormat</span>
            </div>
            <p className="text-xs text-slate-500 max-w-sm leading-relaxed">
              EthioFormat is Ethiopia's premier automated academic thesis and dissertation formatting SaaS platform. Built strictly following institutional guidelines across 22+ Ethiopian public and private universities.
            </p>
          </div>

          <div className="space-y-2">
            <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
              Enforced Standards
            </h4>
            <ul className="text-xs space-y-1.5 text-slate-500">
              <li>• Times New Roman / 12pt Standard</li>
              <li>• 1.5" Left Binding Margins</li>
              <li>• 1.5 Line Spacing & Auto Justify</li>
              <li>• Roman & Arabic Page Numbers</li>
              <li>• Auto TOC & Dot Leaders</li>
            </ul>
          </div>

          <div className="space-y-2">
            <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
              Payment & Security
            </h4>
            <ul className="text-xs space-y-1.5 text-slate-500">
              <li>• Chapa Payment Gateway</li>
              <li>• Telebirr & CBEBirr Supported</li>
              <li>• 3-Page Free Preview Paywall</li>
              <li>• 24-Hour Secure Temporary Storage</li>
              <li>• 100% Zero-Loss Docx Formatting</li>
            </ul>
          </div>
        </div>

        <div className="border-t border-slate-100 pt-6 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-400">
          <div>
            © {new Date().getFullYear()} EthioFormat. All rights reserved. Addis Ababa, Ethiopia.
          </div>
          <div className="flex items-center gap-1 text-slate-500">
            <span>Built with</span>
            <Heart className="h-3.5 w-3.5 text-rose-500 fill-rose-500 inline" />
            <span>for Ethiopian Researchers & Students</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
