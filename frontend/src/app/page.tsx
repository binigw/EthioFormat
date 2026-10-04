"use client";

import React, { useState } from "react";
import { Header } from "@/components/Header";
import { UniversitySelector } from "@/components/UniversitySelector";
import { CustomRulesSelector } from "@/components/CustomRulesSelector";
import { FileUpload } from "@/components/FileUpload";
import { PreviewModal } from "@/components/PreviewModal";
import { Footer } from "@/components/Footer";
import { UNIVERSITY_PRESETS } from "@/lib/presets";
import { UniversityPreset, CustomFormattingRules, PreviewResponse } from "@/types";
import { uploadAndPreviewThesis } from "@/lib/api";
import {
  GraduationCap,
  Sparkles,
  ShieldCheck,
  CheckCircle2,
  FileCheck,
  ArrowRight,
  Loader2,
  BookOpen,
  Award,
  Layers,
  Zap,
} from "lucide-react";

export default function HomePage() {
  const [selectedPreset, setSelectedPreset] = useState<UniversityPreset>(UNIVERSITY_PRESETS[0]);
  const [customRules, setCustomRules] = useState<CustomFormattingRules>({
    font_family: "Times New Roman",
    font_size: 12,
    line_spacing: 1.5,
    margin_preset: "ethiopian_standard",
    toc_mode: "auto_generate",
  });
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const [isProcessing, setIsProcessing] = useState(false);
  const [processStep, setProcessStep] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const [previewData, setPreviewData] = useState<PreviewResponse | null>(null);
  const [isPreviewModalOpen, setIsPreviewModalOpen] = useState(false);

  const handleStartFormatting = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) {
      setErrorMessage("Please select or upload a .docx thesis file to format.");
      return;
    }

    setErrorMessage(null);
    setIsProcessing(true);
    setProcessStep("Parsing document structure & styles...");

    try {
      await new Promise((r) => setTimeout(r, 600));
      setProcessStep("Applying institutional margins, font hierarchy & line spacing...");

      await new Promise((r) => setTimeout(r, 600));
      setProcessStep("Rendering high-resolution 3-page preview & calculating pages...");

      const response = await uploadAndPreviewThesis(
        selectedFile,
        selectedPreset.id,
        selectedPreset.is_custom ? customRules : undefined
      );

      if (response.status === "success") {
        setPreviewData(response);
        setIsPreviewModalOpen(true);
      } else {
        setErrorMessage(response.error_message || "Failed to process thesis formatting.");
      }
    } catch (err: any) {
      setErrorMessage(err.message || "An error occurred during thesis formatting.");
    } finally {
      setIsProcessing(false);
      setProcessStep("");
    }
  };

  const handleReset = () => {
    setSelectedFile(null);
    setPreviewData(null);
    setIsPreviewModalOpen(false);
    setErrorMessage(null);
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 selection:bg-emerald-500 selection:text-white transition-colors duration-200">
      <Header />

      <main className="flex-1">
        {/* Hero Section */}
        <section className="relative overflow-hidden pt-12 pb-16 sm:pt-16 sm:pb-20 border-b border-slate-200/60 dark:border-slate-800/60 bg-gradient-to-b from-white via-slate-50/50 to-emerald-50/20 dark:from-slate-950 dark:via-slate-900/50 dark:to-emerald-950/20">
          <div className="absolute inset-x-0 -top-40 -z-10 transform-gpu overflow-hidden blur-3xl sm:-top-80">
            <div className="relative left-[calc(50%-11rem)] aspect-[1155/678] w-[36.125rem] -translate-x-1/2 rotate-[30deg] bg-gradient-to-tr from-emerald-500 to-teal-400 opacity-20 sm:left-[calc(50%-30rem)] sm:w-[72.1875rem]" />
          </div>

          <div className="container mx-auto max-w-5xl px-4 sm:px-6 text-center space-y-6">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-50 dark:bg-emerald-950/60 border border-emerald-200 dark:border-emerald-800 text-emerald-800 dark:text-emerald-300 text-xs font-semibold shadow-sm">
              <Sparkles className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
              <span>Automated Ethiopian Thesis & Dissertation Formatter</span>
            </div>

            <h1 className="text-3xl sm:text-5xl font-black tracking-tight text-slate-900 dark:text-white leading-tight">
              Format Your Academic Thesis in Seconds.{" "}
              <span className="bg-gradient-to-r from-emerald-600 via-teal-500 to-emerald-500 bg-clip-text text-transparent">
                Zero Layout Errors.
              </span>
            </h1>

            <p className="text-base sm:text-lg text-slate-600 dark:text-slate-300 max-w-2xl mx-auto leading-relaxed">
              Standardized formatting according to official School of Graduate Studies guidelines for <strong>Addis Ababa University</strong>, <strong>Jimma University</strong>, <strong>Hawassa University</strong>, and 20+ Ethiopian higher education institutions.
            </p>

            {/* Badges Bar */}
            <div className="flex flex-wrap items-center justify-center gap-3 sm:gap-6 pt-2 text-xs font-semibold text-slate-600 dark:text-slate-300">
              <div className="flex items-center gap-1.5 bg-white dark:bg-slate-900 px-3 py-1.5 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
                <CheckCircle2 className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
                <span>1.5" Binding Margins</span>
              </div>
              <div className="flex items-center gap-1.5 bg-white dark:bg-slate-900 px-3 py-1.5 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
                <CheckCircle2 className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
                <span>Times New Roman 12pt / 1.5 Spacing</span>
              </div>
              <div className="flex items-center gap-1.5 bg-white dark:bg-slate-900 px-3 py-1.5 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
                <CheckCircle2 className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
                <span>Auto Chapter TOC & Numbering</span>
              </div>
              <div className="flex items-center gap-1.5 bg-white dark:bg-slate-900 px-3 py-1.5 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
                <CheckCircle2 className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
                <span>Free 3-Page Instant Preview</span>
              </div>
            </div>
          </div>
        </section>

        {/* Formatter Main Card Section */}
        <section className="container mx-auto max-w-4xl px-4 sm:px-6 -mt-8 mb-20 relative z-20">
          <div className="bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-2xl p-6 sm:p-8 md:p-10 space-y-8 transition-colors duration-200">
            <div className="border-b border-slate-100 dark:border-slate-800 pb-5">
              <h2 className="text-xl font-black text-slate-900 dark:text-white tracking-tight flex items-center gap-2">
                <BookOpen className="h-5 w-5 text-emerald-600 dark:text-emerald-400" />
                <span>Step 1: Select University & Upload Document</span>
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                Choose your university from the strict dropdown menu to apply standardized thesis guidelines automatically.
              </p>
            </div>

            <form onSubmit={handleStartFormatting} className="space-y-6">
              {/* Primary University Selection Dropdown */}
              <UniversitySelector
                selectedId={selectedPreset.id}
                onSelect={(preset) => setSelectedPreset(preset)}
                disabled={isProcessing}
              />

              {/* Mode B: Secondary Dropdowns (Unlocked only if Custom Setup is chosen) */}
              {selectedPreset.is_custom && (
                <CustomRulesSelector
                  rules={customRules}
                  onChange={(updated) => setCustomRules(updated)}
                  disabled={isProcessing}
                />
              )}

              {/* File Uploader */}
              <FileUpload
                file={selectedFile}
                onFileSelect={(file) => setSelectedFile(file)}
                disabled={isProcessing}
              />

              {errorMessage && (
                <div className="p-4 rounded-xl bg-rose-50 dark:bg-rose-950/50 border border-rose-200 dark:border-rose-900 text-xs sm:text-sm text-rose-800 dark:text-rose-300 flex items-center gap-2.5">
                  <span className="font-bold">Error:</span>
                  <span>{errorMessage}</span>
                </div>
              )}

              {/* Submit CTA Button */}
              <div className="pt-2">
                <button
                  type="submit"
                  disabled={!selectedFile || isProcessing}
                  className="w-full py-4 px-6 rounded-2xl bg-gradient-to-r from-emerald-600 via-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 text-white font-extrabold text-base shadow-xl shadow-emerald-600/25 hover:shadow-emerald-600/40 hover:scale-[1.01] active:scale-[0.99] transition-all flex items-center justify-center gap-3 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
                >
                  {isProcessing ? (
                    <>
                      <Loader2 className="h-5 w-5 animate-spin" />
                      <span>{processStep || "Formatting Thesis Document..."}</span>
                    </>
                  ) : (
                    <>
                      <Sparkles className="h-5 w-5" />
                      <span>Format Thesis & View 3-Page Free Preview</span>
                      <ArrowRight className="h-5 w-5" />
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </section>

        {/* Feature Comparison Section */}
        <section className="container mx-auto max-w-5xl px-4 sm:px-6 py-12 mb-16">
          <div className="text-center space-y-3 mb-10">
            <h3 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white">
              Why Ethiopian Universities Reject Unformatted Theses
            </h3>
            <p className="text-sm text-slate-500 dark:text-slate-400 max-w-xl mx-auto">
              EthioFormat automatically fixes the 6 most common margin and style errors that cause thesis rejections at the Graduate Office.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-3">
              <div className="w-10 h-10 rounded-xl bg-emerald-100 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-400 flex items-center justify-center font-bold">
                1
              </div>
              <h4 className="font-bold text-slate-900 dark:text-white">1.5" Left Binding Margins</h4>
              <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
                Standard Word margins (1.0" Left) cut off text when binding thesis hardcovers. EthioFormat sets exactly 1.5" left margin across all sections.
              </p>
            </div>

            <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-3">
              <div className="w-10 h-10 rounded-xl bg-emerald-100 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-400 flex items-center justify-center font-bold">
                2
              </div>
              <h4 className="font-bold text-slate-900 dark:text-white">Strict Roman & Arabic Page Numbers</h4>
              <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
                Preliminary pages (Approval, Dedication, Abstract, TOC) require Roman numerals (i, ii, iii), while Chapter 1 starts at Arabic 1.
              </p>
            </div>

            <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-3">
              <div className="w-10 h-10 rounded-xl bg-emerald-100 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-400 flex items-center justify-center font-bold">
                3
              </div>
              <h4 className="font-bold text-slate-900 dark:text-white">Synchronized Dot-Leader TOC</h4>
              <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
                Manual spaces in Tables of Contents get misaligned. Our engine builds formatted dot leaders that perfectly align chapter numbers to page edges.
              </p>
            </div>
          </div>
        </section>
      </main>

      {/* Preview Modal Popup */}
      {previewData && (
        <PreviewModal
          isOpen={isPreviewModalOpen}
          onClose={() => setIsPreviewModalOpen(false)}
          previewData={previewData}
          onReset={handleReset}
        />
      )}

      <Footer />
    </div>
  );
}
