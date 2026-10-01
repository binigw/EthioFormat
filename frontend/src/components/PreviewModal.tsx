"use client";

import React, { useState } from "react";
import { PreviewResponse, PaymentVerificationResponse } from "@/types";
import { PageViewer } from "@/components/PageViewer";
import { BlurPaywallHook } from "@/components/BlurPaywallHook";
import { PaymentModal } from "@/components/PaymentModal";
import { DownloadCard } from "@/components/DownloadCard";
import { X, Building2, FileCheck2, Sparkles, Layers } from "lucide-react";

interface PreviewModalProps {
  isOpen: boolean;
  onClose: () => void;
  previewData: PreviewResponse;
  onReset: () => void;
}

export function PreviewModal({
  isOpen,
  onClose,
  previewData,
  onReset,
}: PreviewModalProps) {
  const [isPaymentModalOpen, setIsPaymentModalOpen] = useState(false);
  const [paymentResult, setPaymentResult] = useState<PaymentVerificationResponse | null>(null);

  if (!isOpen) return null;

  const handlePaymentSuccess = (data: PaymentVerificationResponse) => {
    setPaymentResult(data);
    setIsPaymentModalOpen(false);

    // Trigger automatic browser download
    if (data.download_url) {
      let downloadUrl = data.download_url;
      if (downloadUrl.startsWith("/api/download/")) {
        downloadUrl = downloadUrl.replace("/api/download/", "/api/backend/download/");
      }
      const link = document.createElement("a");
      link.href = downloadUrl;
      link.download = data.file_name || "Formatted_Thesis.docx";
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  };

  return (
    <>
      <div className="fixed inset-0 z-40 flex items-center justify-center p-2 sm:p-4 md:p-6 bg-slate-950/80 backdrop-blur-md overflow-y-auto animate-in fade-in-50 duration-200">
        <div className="relative w-full max-w-5xl my-8 bg-white rounded-3xl shadow-2xl border border-slate-200 overflow-hidden flex flex-col max-h-[92vh]">
          {/* Top Bar */}
          <div className="px-6 py-4 bg-slate-900 text-white flex items-center justify-between border-b border-slate-800 flex-shrink-0">
            <div className="flex items-center gap-3 overflow-hidden">
              <div className="p-2 rounded-xl bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 flex-shrink-0">
                <FileCheck2 className="h-5 w-5" />
              </div>
              <div className="truncate">
                <div className="flex items-center gap-2">
                  <h3 className="font-bold text-base truncate">
                    {previewData.metadata.filename}
                  </h3>
                  <span className="hidden sm:inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 text-xs font-semibold border border-emerald-500/30">
                    <Sparkles className="h-3 w-3" /> Ready
                  </span>
                </div>
                <div className="text-xs text-slate-400 flex items-center gap-2 truncate">
                  <span>{previewData.metadata.university}</span>
                  <span>•</span>
                  <span className="text-emerald-400 font-semibold">{previewData.total_pages} Total Pages</span>
                </div>
              </div>
            </div>

            <button
              type="button"
              onClick={onClose}
              className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-xl transition-colors ml-4"
              title="Close Preview"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          {/* Modal Scrollable Content */}
          <div className="p-4 sm:p-6 md:p-8 overflow-y-auto flex-1 bg-slate-50">
            {paymentResult && paymentResult.verified ? (
              <DownloadCard
                paymentData={paymentResult}
                fileName={previewData.metadata.filename}
                onReset={() => {
                  setPaymentResult(null);
                  onReset();
                }}
              />
            ) : (
              <div className="max-w-4xl mx-auto space-y-6">
                {/* Free Preview Banner */}
                <div className="flex items-center justify-between p-3.5 rounded-2xl bg-emerald-50 border border-emerald-200 text-emerald-950 text-xs sm:text-sm">
                  <div className="flex items-center gap-2">
                    <div className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-ping" />
                    <span className="font-bold">
                      Free Preview (First 3 Pages: Cover, Approval Sheet & TOC)
                    </span>
                  </div>
                  <span className="font-mono text-emerald-800 font-semibold">
                    100% Guaranteed Layout
                  </span>
                </div>

                {/* High-Resolution Document Page Viewer */}
                <PageViewer
                  previewPages={previewData.preview_pages}
                  totalPages={previewData.total_pages}
                />

                {/* Frosted Blur Paywall Hook */}
                <BlurPaywallHook
                  totalPages={previewData.total_pages}
                  pricing={previewData.pricing}
                  onPayClick={() => setIsPaymentModalOpen(true)}
                />
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Payment Initiation Modal */}
      {isPaymentModalOpen && (
        <PaymentModal
          isOpen={isPaymentModalOpen}
          onClose={() => setIsPaymentModalOpen(false)}
          sessionId={previewData.session_id}
          totalPages={previewData.total_pages}
          pricing={previewData.pricing}
          universityName={previewData.metadata.university}
          onPaymentSuccess={handlePaymentSuccess}
        />
      )}
    </>
  );
}
