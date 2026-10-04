"use client";

import React from "react";
import { CustomFormattingRules } from "@/types";
import { SlidersHorizontal, Type, AlignJustify, MoveHorizontal, ListTree } from "lucide-react";

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
  const handleChange = <K extends keyof CustomFormattingRules>(
    key: K,
    value: CustomFormattingRules[K]
  ) => {
    onChange({
      ...rules,
      [key]: value,
    });
  };

  return (
    <div className="p-4 sm:p-5 rounded-2xl bg-amber-50/50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800/60 space-y-4 animate-in fade-in-50 duration-200">
      <div className="flex items-center justify-between border-b border-amber-200/60 dark:border-amber-800/60 pb-3">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-amber-100 dark:bg-amber-900/60 text-amber-800 dark:text-amber-300">
            <SlidersHorizontal className="h-4 w-4" />
          </div>
          <div>
            <h4 className="font-bold text-sm text-amber-950 dark:text-amber-200">
              Mode B: Secondary Dropdowns (Locked Custom Rules)
            </h4>
            <p className="text-xs text-amber-800 dark:text-amber-400">
              Zero manual typing. All parameters strictly constrained to valid academic presets.
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3.5">
        {/* Font Family */}
        <div className="space-y-1">
          <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-1">
            <Type className="h-3.5 w-3.5 text-amber-600 dark:text-amber-400" />
            <span>Font Family</span>
          </label>
          <select
            disabled={disabled}
            value={rules.font_family}
            onChange={(e) =>
              handleChange(
                "font_family",
                e.target.value as CustomFormattingRules["font_family"]
              )
            }
            className="w-full px-3 py-2 text-xs bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg focus:outline-none focus:border-emerald-500 font-medium text-slate-900 dark:text-slate-100"
          >
            <option value="Times New Roman">Times New Roman (Standard)</option>
            <option value="Arial">Arial (Clean Modern)</option>
          </select>
        </div>

        {/* Font Size */}
        <div className="space-y-1">
          <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-1">
            <Type className="h-3.5 w-3.5 text-amber-600 dark:text-amber-400" />
            <span>Body Font Size</span>
          </label>
          <select
            disabled={disabled}
            value={rules.font_size}
            onChange={(e) =>
              handleChange(
                "font_size",
                Number(e.target.value) as CustomFormattingRules["font_size"]
              )
            }
            className="w-full px-3 py-2 text-xs bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg focus:outline-none focus:border-emerald-500 font-medium text-slate-900 dark:text-slate-100"
          >
            <option value={12}>12 pt (Official Body Standard)</option>
            <option value={11}>11 pt (Compact Standard)</option>
          </select>
        </div>

        {/* Line Spacing */}
        <div className="space-y-1">
          <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-1">
            <AlignJustify className="h-3.5 w-3.5 text-amber-600 dark:text-amber-400" />
            <span>Line Spacing</span>
          </label>
          <select
            disabled={disabled}
            value={rules.line_spacing}
            onChange={(e) =>
              handleChange(
                "line_spacing",
                Number(e.target.value) as CustomFormattingRules["line_spacing"]
              )
            }
            className="w-full px-3 py-2 text-xs bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg focus:outline-none focus:border-emerald-500 font-medium text-slate-900 dark:text-slate-100"
          >
            <option value={1.5}>1.5 Lines (Ethiopian Standard)</option>
            <option value={2.0}>2.0 Lines (Double Spacing)</option>
            <option value={1.0}>1.0 Line (Single Spacing)</option>
          </select>
        </div>

        {/* Margin Preset */}
        <div className="space-y-1 sm:col-span-2 lg:col-span-1">
          <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-1">
            <MoveHorizontal className="h-3.5 w-3.5 text-amber-600 dark:text-amber-400" />
            <span>Margin Configuration</span>
          </label>
          <select
            disabled={disabled}
            value={rules.margin_preset}
            onChange={(e) =>
              handleChange(
                "margin_preset",
                e.target.value as CustomFormattingRules["margin_preset"]
              )
            }
            className="w-full px-3 py-2 text-xs bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg focus:outline-none focus:border-emerald-500 font-medium text-slate-900 dark:text-slate-100"
          >
            <option value="ethiopian_standard">
              Ethiopian Standard (Left 1.5", Others 1.0")
            </option>
            <option value="equal_margins">
              Equal Margins (1.0" All Sides)
            </option>
          </select>
        </div>

        {/* Table of Contents */}
        <div className="space-y-1 sm:col-span-2 lg:col-span-2">
          <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-1">
            <ListTree className="h-3.5 w-3.5 text-amber-600 dark:text-amber-400" />
            <span>Table of Contents (TOC) Handling</span>
          </label>
          <select
            disabled={disabled}
            value={rules.toc_mode}
            onChange={(e) =>
              handleChange(
                "toc_mode",
                e.target.value as CustomFormattingRules["toc_mode"]
              )
            }
            className="w-full px-3 py-2 text-xs bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg focus:outline-none focus:border-emerald-500 font-medium text-slate-900 dark:text-slate-100"
          >
            <option value="auto_generate">
              Auto-Generate Synchronized TOC with Dot Leaders
            </option>
            <option value="keep_existing">
              Keep Existing Document TOC Structure
            </option>
          </select>
        </div>
      </div>
    </div>
  );
}
