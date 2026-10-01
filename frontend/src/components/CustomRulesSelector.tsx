"use client";

import React from "react";
import { CustomFormattingRules } from "@/types";
import {
  CUSTOM_FONT_FAMILIES,
  CUSTOM_FONT_SIZES,
  CUSTOM_LINE_SPACINGS,
  CUSTOM_MARGIN_PRESETS,
  CUSTOM_TOC_MODES,
} from "@/lib/presets";
import { SlidersHorizontal, Type, Space, LayoutTemplate, ListTree } from "lucide-react";

interface CustomRulesSelectorProps {
  rules: CustomFormattingRules;
  onChange: (updated: CustomFormattingRules) => void;
  disabled?: boolean;
}

export function CustomRulesSelector({
  rules,
  onChange,
  disabled = false,
}: CustomRulesSelectorProps) {
  const updateRule = <K extends keyof CustomFormattingRules>(
    key: K,
    value: CustomFormattingRules[K]
  ) => {
    onChange({
      ...rules,
      [key]: value,
    });
  };

  return (
    <div className="p-4 sm:p-5 rounded-xl border border-amber-200 bg-amber-50/40 space-y-4 animate-in fade-in-50 duration-200">
      <div className="flex items-center justify-between border-b border-amber-200/80 pb-3">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-amber-100 text-amber-800">
            <SlidersHorizontal className="h-4 w-4" />
          </div>
          <div>
            <h4 className="text-sm font-bold text-amber-950">
              Mode B: Custom Dropdown Specifications (የተለየ ህግ)
            </h4>
            <p className="text-xs text-amber-800">
              Select specific guidelines via locked dropdown options (Zero manual entry)
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {/* Font Family Dropdown */}
        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-slate-800 flex items-center gap-1.5">
            <Type className="h-3.5 w-3.5 text-slate-600" />
            <span>Font Family (የፊደል ዓይነት)</span>
          </label>
          <div className="relative">
            <select
              disabled={disabled}
              value={rules.font_family}
              onChange={(e) => updateRule("font_family", e.target.value as any)}
              className="w-full px-3 py-2 text-sm bg-white border border-slate-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-amber-500/30 focus:border-amber-600 disabled:opacity-60"
            >
              {CUSTOM_FONT_FAMILIES.map((f) => (
                <option key={f.value} value={f.value}>
                  {f.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Font Size Dropdown */}
        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-slate-800 flex items-center gap-1.5">
            <Type className="h-3.5 w-3.5 text-slate-600" />
            <span>Font Size (የፊደል መጠን)</span>
          </label>
          <select
            disabled={disabled}
            value={rules.font_size}
            onChange={(e) => updateRule("font_size", Number(e.target.value) as any)}
            className="w-full px-3 py-2 text-sm bg-white border border-slate-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-amber-500/30 focus:border-amber-600 disabled:opacity-60"
          >
            {CUSTOM_FONT_SIZES.map((s) => (
              <option key={s.value} value={s.value}>
                {s.label}
              </option>
            ))}
          </select>
        </div>

        {/* Line Spacing Dropdown */}
        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-slate-800 flex items-center gap-1.5">
            <Space className="h-3.5 w-3.5 text-slate-600" />
            <span>Line Spacing (የመስመር ክፍተት)</span>
          </label>
          <select
            disabled={disabled}
            value={rules.line_spacing}
            onChange={(e) => updateRule("line_spacing", Number(e.target.value) as any)}
            className="w-full px-3 py-2 text-sm bg-white border border-slate-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-amber-500/30 focus:border-amber-600 disabled:opacity-60"
          >
            {CUSTOM_LINE_SPACINGS.map((l) => (
              <option key={l.value} value={l.value}>
                {l.label}
              </option>
            ))}
          </select>
        </div>

        {/* Margins Dropdown */}
        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-slate-800 flex items-center gap-1.5">
            <LayoutTemplate className="h-3.5 w-3.5 text-slate-600" />
            <span>Margin Preset (የገጽ ህዳግ)</span>
          </label>
          <select
            disabled={disabled}
            value={rules.margin_preset}
            onChange={(e) => updateRule("margin_preset", e.target.value as any)}
            className="w-full px-3 py-2 text-sm bg-white border border-slate-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-amber-500/30 focus:border-amber-600 disabled:opacity-60"
          >
            {CUSTOM_MARGIN_PRESETS.map((m) => (
              <option key={m.value} value={m.value}>
                {m.label}
              </option>
            ))}
          </select>
        </div>

        {/* Table of Contents Dropdown */}
        <div className="space-y-1.5 sm:col-span-2">
          <label className="text-xs font-semibold text-slate-800 flex items-center gap-1.5">
            <ListTree className="h-3.5 w-3.5 text-slate-600" />
            <span>Table of Contents Mode (የማውጫ ህግ)</span>
          </label>
          <select
            disabled={disabled}
            value={rules.toc_mode}
            onChange={(e) => updateRule("toc_mode", e.target.value as any)}
            className="w-full px-3 py-2 text-sm bg-white border border-slate-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-amber-500/30 focus:border-amber-600 disabled:opacity-60"
          >
            {CUSTOM_TOC_MODES.map((t) => (
              <option key={t.value} value={t.value}>
                {t.label}
              </option>
            ))}
          </select>
        </div>
      </div>
    </div>
  );
}
