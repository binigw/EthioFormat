"use client";

import React, { useState } from "react";
import { UNIVERSITY_PRESETS } from "@/lib/presets";
import { UniversityPreset } from "@/types";
import { Building2, ChevronDown, Check, SlidersHorizontal, Search } from "lucide-react";

interface UniversitySelectorProps {
  selectedId: string;
  onSelect: (preset: UniversityPreset) => void;
  disabled?: boolean;
}

export function UniversitySelector({
  selectedId,
  onSelect,
  disabled = false,
}: UniversitySelectorProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");

  const selectedPreset =
    UNIVERSITY_PRESETS.find((p) => p.id === selectedId) || UNIVERSITY_PRESETS[0];

  const filteredPresets = UNIVERSITY_PRESETS.filter((p) =>
    p.display_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    p.name_en.toLowerCase().includes(searchTerm.toLowerCase()) ||
    p.name_am.includes(searchTerm)
  );

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <label className="text-sm font-semibold text-slate-900 dark:text-white flex items-center gap-1.5">
          <Building2 className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
          <span>University Guidelines Preset (የዩኒቨርሲቲ ምርጫ)</span>
          <span className="text-rose-500">*</span>
        </label>
        <span className="text-xs text-slate-500 dark:text-slate-400">
          Strict Dropdown Selection Only
        </span>
      </div>

      <div className="relative">
        <button
          type="button"
          disabled={disabled}
          onClick={() => setIsOpen(!isOpen)}
          className={`w-full flex items-center justify-between px-4 py-3 bg-white dark:bg-slate-900 border rounded-xl text-left shadow-sm transition-all focus:outline-none focus:ring-2 focus:ring-emerald-500/20 ${
            isOpen
              ? "border-emerald-600 ring-2 ring-emerald-500/20"
              : "border-slate-300 dark:border-slate-700 hover:border-slate-400 dark:hover:border-slate-600"
          } ${disabled ? "opacity-60 cursor-not-allowed bg-slate-50 dark:bg-slate-800" : ""}`}
        >
          <div className="flex items-center gap-3 overflow-hidden">
            <div className={`p-2 rounded-lg flex-shrink-0 ${
              selectedPreset.is_custom 
                ? 'bg-amber-100 dark:bg-amber-950/80 text-amber-700 dark:text-amber-400' 
                : 'bg-emerald-100 dark:bg-emerald-950/80 text-emerald-700 dark:text-emerald-400'
            }`}>
              {selectedPreset.is_custom ? (
                <SlidersHorizontal className="h-4 w-4" />
              ) : (
                <Building2 className="h-4 w-4" />
              )}
            </div>
            <div className="truncate">
              <div className="font-medium text-slate-900 dark:text-white truncate">
                {selectedPreset.name_en}
              </div>
              <div className="text-xs text-emerald-700 dark:text-emerald-400 font-medium truncate">
                {selectedPreset.name_am}
              </div>
            </div>
          </div>
          <ChevronDown
            className={`h-4 w-4 text-slate-500 dark:text-slate-400 transition-transform duration-200 flex-shrink-0 ml-2 ${
              isOpen ? "rotate-180 text-emerald-600 dark:text-emerald-400" : ""
            }`}
          />
        </button>

        {isOpen && !disabled && (
          <>
            <div
              className="fixed inset-0 z-20"
              onClick={() => setIsOpen(false)}
            />
            <div className="absolute z-30 mt-2 w-full bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-2xl overflow-hidden animate-in fade-in-50 zoom-in-95 duration-100">
              <div className="p-2 border-b border-slate-100 dark:border-slate-800 bg-slate-50/70 dark:bg-slate-950/50">
                <div className="relative flex items-center">
                  <Search className="absolute left-3 h-4 w-4 text-slate-400" />
                  <input
                    type="text"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    placeholder="Search university preset (ፈልግ)..."
                    className="w-full pl-9 pr-3 py-1.5 text-xs bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg focus:outline-none focus:border-emerald-500 text-slate-900 dark:text-white"
                    autoFocus
                  />
                </div>
              </div>

              <div className="max-h-72 overflow-y-auto divide-y divide-slate-100 dark:divide-slate-800 p-1">
                {filteredPresets.length === 0 ? (
                  <div className="p-4 text-center text-xs text-slate-500 dark:text-slate-400">
                    No university matches your search.
                  </div>
                ) : (
                  filteredPresets.map((preset) => {
                    const isSelected = preset.id === selectedId;
                    return (
                      <button
                        key={preset.id}
                        type="button"
                        onClick={() => {
                          onSelect(preset);
                          setIsOpen(false);
                          setSearchTerm("");
                        }}
                        className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-left transition-colors cursor-pointer ${
                          isSelected
                            ? "bg-emerald-50 dark:bg-emerald-950/60 text-emerald-950 dark:text-emerald-200 font-medium"
                            : "hover:bg-slate-50 dark:hover:bg-slate-800/60 text-slate-800 dark:text-slate-200"
                        }`}
                      >
                        <div className="flex items-center gap-2.5 min-w-0 pr-2">
                          <span className={`text-xs px-1.5 py-0.5 rounded font-mono font-semibold flex-shrink-0 ${
                            preset.is_custom 
                              ? 'bg-amber-100 dark:bg-amber-950 text-amber-800 dark:text-amber-300' 
                              : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400'
                          }`}>
                            {preset.is_custom ? "⚙️" : preset.id.toUpperCase()}
                          </span>
                          <div className="truncate">
                            <div className="text-sm truncate leading-snug">
                              {preset.name_en}
                            </div>
                            <div className="text-xs text-slate-500 dark:text-slate-400 truncate">
                              {preset.name_am}
                            </div>
                          </div>
                        </div>

                        {isSelected && (
                          <Check className="h-4 w-4 text-emerald-600 dark:text-emerald-400 flex-shrink-0" />
                        )}
                      </button>
                    );
                  })
                )}
              </div>
            </div>
          </>
        )}
      </div>

      {!selectedPreset.is_custom && (
        <div className="p-3 rounded-lg bg-emerald-50/60 dark:bg-emerald-950/30 border border-emerald-100 dark:border-emerald-900/60 text-xs text-slate-700 dark:text-slate-300 space-y-1">
          <div className="font-semibold text-emerald-900 dark:text-emerald-300 flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-600 dark:bg-emerald-400"></span>
            Enforced Institutional Standard:
          </div>
          <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-slate-600 dark:text-slate-400 pl-3">
            <div>• Font: <strong className="text-slate-900 dark:text-slate-200">Times New Roman (12pt Body / 14pt H1)</strong></div>
            <div>• Line Spacing: <strong className="text-slate-900 dark:text-slate-200">1.5 Lines (Justified)</strong></div>
            <div>• Left Margin: <strong className="text-slate-900 dark:text-slate-200">1.5" Binding Edge</strong></div>
            <div>• Top / Right / Bottom: <strong className="text-slate-900 dark:text-slate-200">1.0" Standard</strong></div>
          </div>
        </div>
      )}
    </div>
  );
}
