"use client";

import React, { useState } from "react";
import { ZoomIn, ZoomOut, RotateCcw, ChevronLeft, ChevronRight, FileText, CheckCircle2 } from "lucide-react";

interface PageViewerProps {
  previewPages: string[];
  totalPages: number;
}

export function PageViewer({ previewPages, totalPages }: PageViewerProps) {
  const [zoom, setZoom] = useState(1.0);
  const [activeTab, setActiveTab] = useState<number>(0);

  const pageLabels = [
    { title: "Page 1: Cover Page", desc: "Title, Author, Institution, Date" },
    { title: "Page 2: Approval Sheet", desc: "Examining Committee & Signatures" },
    { title: "Page 3: Table of Contents", desc: "Chapters, Sections & Dot Leaders" },
  ];

  const handleZoomIn = () => setZoom((prev) => Math.min(prev + 0.2, 1.8));
  const handleZoomOut = () => setZoom((prev) => Math.max(prev - 0.2, 0.6));
  const handleResetZoom = () => setZoom(1.0);

  return (
    <div className="space-y-4">
      {/* Controls Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-3 bg-slate-100/80 rounded-xl border border-slate-200">
        {/* Page Selector Tabs */}
        <div className="flex items-center gap-1.5 overflow-x-auto">
          {previewPages.map((_, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => setActiveTab(idx)}
              className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-all flex items-center gap-1.5 whitespace-nowrap ${
                activeTab === idx
                  ? "bg-emerald-600 text-white shadow-sm"
                  : "bg-white text-slate-700 hover:bg-slate-200/80 border border-slate-200"
              }`}
            >
              <FileText className="h-3.5 w-3.5" />
              <span>Page {idx + 1}</span>
            </button>
          ))}
          <div className="px-2.5 py-1 text-xs font-medium text-slate-500 bg-slate-200/60 rounded-lg whitespace-nowrap">
            + {Math.max(0, totalPages - 3)} Locked Pages
          </div>
        </div>

        {/* Zoom Controls */}
        <div className="flex items-center gap-1 bg-white p-1 rounded-lg border border-slate-200 shadow-sm ml-auto">
          <button
            type="button"
            onClick={handleZoomOut}
            className="p-1.5 text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded"
            title="Zoom Out"
          >
            <ZoomOut className="h-4 w-4" />
          </button>
          <span className="text-xs font-mono px-2 text-slate-700 font-semibold">
            {Math.round(zoom * 100)}%
          </span>
          <button
            type="button"
            onClick={handleZoomIn}
            className="p-1.5 text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded"
            title="Zoom In"
          >
            <ZoomIn className="h-4 w-4" />
          </button>
          <button
            type="button"
            onClick={handleResetZoom}
            className="p-1.5 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded ml-0.5 border-l border-slate-200"
            title="Reset Zoom"
          >
            <RotateCcw className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>

      {/* Main Single Page Focus & Preview */}
      <div className="space-y-2">
        <div className="flex items-center justify-between text-xs px-2 text-slate-600">
          <span className="font-semibold text-slate-900">
            {pageLabels[activeTab]?.title || `Page ${activeTab + 1}`}
          </span>
          <span>{pageLabels[activeTab]?.desc}</span>
        </div>

        <div className="relative bg-slate-200/60 rounded-2xl p-4 sm:p-8 flex justify-center items-center overflow-x-auto min-h-[520px] border border-slate-300/80 shadow-inner">
          {previewPages[activeTab] ? (
            <div
              style={{ transform: `scale(${zoom})`, transformOrigin: "top center" }}
              className="transition-transform duration-150 ease-out shadow-2xl rounded-lg overflow-hidden bg-white max-w-full"
            >
              <img
                src={previewPages[activeTab]}
                alt={`Preview Page ${activeTab + 1}`}
                className="w-auto max-h-[750px] object-contain select-none"
              />
            </div>
          ) : (
            <div className="text-slate-400 text-sm">Preview page not available</div>
          )}
        </div>
      </div>

      {/* 3-Page Grid View Option for quick inspection */}
      <div className="pt-2">
        <div className="text-xs font-bold text-slate-700 mb-2 uppercase tracking-wider">
          All Free Preview Pages (1 - 3)
        </div>
        <div className="grid grid-cols-3 gap-3">
          {previewPages.map((pageSrc, idx) => (
            <div
              key={idx}
              onClick={() => setActiveTab(idx)}
              className={`p-2 rounded-xl border cursor-pointer transition-all ${
                activeTab === idx
                  ? "border-emerald-500 ring-2 ring-emerald-500/20 bg-emerald-50/30"
                  : "border-slate-200 bg-white hover:border-slate-300"
              }`}
            >
              <div className="aspect-[1/1.3] bg-slate-100 rounded overflow-hidden shadow-sm flex items-center justify-center">
                <img
                  src={pageSrc}
                  alt={`Thumbnail ${idx + 1}`}
                  className="w-full h-full object-cover object-top"
                />
              </div>
              <div className="mt-1.5 text-[11px] font-semibold text-center text-slate-800 flex items-center justify-center gap-1">
                <span>Page {idx + 1}</span>
                {activeTab === idx && <CheckCircle2 className="h-3 w-3 text-emerald-600" />}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
