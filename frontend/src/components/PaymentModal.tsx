"use client";

import React, { useState, useEffect, useRef } from "react";
import { formatETB } from "@/lib/utils";
import { PricingDetail, TransactionStatusResponse, CBEPaymentInitiationResponse } from "@/types";
import { initiateCBEPayment, submitCBETransaction, checkTransactionStatus } from "@/lib/api";
import {
  X,
  Building,
  ShieldCheck,
  CheckCircle2,
  Loader2,
  ArrowRight,
  Copy,
  Check,
  Lock,
  Smartphone,
  AlertCircle,
  Clock,
} from "lucide-react";
import confetti from "canvas-confetti";

interface PaymentModalProps {
  isOpen: boolean;
  onClose: () => void;
  sessionId: string;
  totalPages: number;
  pricing: PricingDetail;
  universityName: string;
  onPaymentSuccess: (data: TransactionStatusResponse) => void;
}

export function PaymentModal({
  isOpen,
  onClose,
  sessionId,
  totalPages,
  pricing,
  universityName,
  onPaymentSuccess,
}: PaymentModalProps) {
  const [initData, setInitData] = useState<CBEPaymentInitiationResponse | null>(null);
  const [isInitializing, setIsInitializing] = useState(true);

  // User inputs
  const [transactionRef, setTransactionRef] = useState("");
  const [payerName, setPayerName] = useState("");
  const [payerPhone, setPayerPhone] = useState("");

  // Validation & Status States
  const [txnInputError, setTxnInputError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isPolling, setIsPolling] = useState(false);
  const [statusMessage, setStatusMessage] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [copiedAccount, setCopiedAccount] = useState(false);
  const [copiedAmount, setCopiedAmount] = useState(false);

  const pollingTimerRef = useRef<NodeJS.Timeout | null>(null);

  // 1. Initiate CBE Details on modal open
  useEffect(() => {
    if (!isOpen) return;

    let mounted = true;
    setIsInitializing(true);
    setErrorMessage(null);
    setTxnInputError(null);

    initiateCBEPayment(sessionId)
      .then((data) => {
        if (mounted) {
          setInitData(data);
          setIsInitializing(false);
        }
      })
      .catch((err) => {
        if (mounted) {
          setErrorMessage(err.message || "Failed to load CBE payment details.");
          setIsInitializing(false);
        }
      });

    return () => {
      mounted = false;
      if (pollingTimerRef.current) clearInterval(pollingTimerRef.current);
    };
  }, [isOpen, sessionId]);

  // Polling loop
  const startPollingStatus = () => {
    setIsPolling(true);
    setStatusMessage("Listening for CBE confirmation webhook... This updates automatically upon payment.");

    if (pollingTimerRef.current) clearInterval(pollingTimerRef.current);

    pollingTimerRef.current = setInterval(async () => {
      try {
        const res = await checkTransactionStatus(sessionId);
        if (res.status === "approved" && res.verified) {
          if (pollingTimerRef.current) clearInterval(pollingTimerRef.current);
          setIsPolling(false);
          setStatusMessage("Payment Verified! Unlocking full formatted thesis...");

          // Confetti celebration
          confetti({
            particleCount: 90,
            spread: 75,
            origin: { y: 0.6 },
          });

          await new Promise((r) => setTimeout(r, 600));
          onPaymentSuccess(res);
        } else if (res.status === "failed") {
          if (pollingTimerRef.current) clearInterval(pollingTimerRef.current);
          setIsPolling(false);
          setErrorMessage(res.message || "Payment verification failed. Please check the amount transferred.");
        }
      } catch (e) {
        // Continue polling silently
      }
    }, 2500);
  };

  const handleSubmitTxn = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    // Custom Validation: Check if Transaction ID is empty or whitespace
    if (!transactionRef || !transactionRef.trim()) {
      setTxnInputError("Please enter your Transaction ID.");
      return;
    }

    setTxnInputError(null);
    setIsSubmitting(true);
    setStatusMessage("Registering CBE Transaction ID...");

    try {
      const res = await submitCBETransaction(
        sessionId,
        transactionRef.trim(),
        payerName.trim() || undefined,
        payerPhone.trim() || undefined
      );

      setIsSubmitting(false);

      if (res.status === "approved" && res.download_url) {
        confetti({
          particleCount: 90,
          spread: 75,
          origin: { y: 0.6 },
        });
        onPaymentSuccess({
          status: "approved",
          session_id: sessionId,
          transaction_ref: transactionRef,
          amount_expected: res.amount_expected,
          verified: true,
          download_url: res.download_url,
          file_name: res.file_name,
        });
      } else {
        // Start polling for the incoming email webhook / IMAP
        startPollingStatus();
      }
    } catch (err: any) {
      setIsSubmitting(false);
      setErrorMessage(err.message || "Failed to submit transaction reference.");
    }
  };

  const copyToClipboard = (text: string, type: "account" | "amount") => {
    navigator.clipboard.writeText(text);
    if (type === "account") {
      setCopiedAccount(true);
      setTimeout(() => setCopiedAccount(false), 2000);
    } else {
      setCopiedAmount(true);
      setTimeout(() => setCopiedAmount(false), 2000);
    }
  };

  if (!isOpen) return null;

  const cbeAccNumber = initData?.cbe_account_number || "1000123456789";
  const cbeAccName = initData?.cbe_account_name || "EthioFormat / Thesis Automation Services";
  const exactAmount = initData?.amount_expected ?? pricing.total_fee;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-slate-950/85 backdrop-blur-md animate-in fade-in-50 duration-200 overflow-y-auto">
      <div className="relative w-full max-w-lg my-6 bg-slate-900 text-slate-100 rounded-3xl shadow-2xl border border-slate-800 overflow-hidden flex flex-col">
        {/* Header */}
        <div className="bg-gradient-to-r from-purple-950 via-indigo-950 to-purple-900 px-6 py-5 text-white flex items-center justify-between border-b border-purple-900/50">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-2xl bg-white/10 backdrop-blur-md text-amber-300 border border-white/10 flex-shrink-0">
              <Building className="h-6 w-6" />
            </div>
            <div>
              <h3 className="font-bold text-lg leading-tight flex items-center gap-2">
                <span>CBE Birr / Bank Transfer</span>
                <span className="text-[10px] uppercase tracking-wider bg-amber-400 text-purple-950 font-black px-2 py-0.5 rounded-full">
                  Official
                </span>
              </h3>
              <p className="text-xs text-purple-300">{universityName}</p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            disabled={isSubmitting || isPolling}
            className="p-1.5 rounded-lg text-white/80 hover:text-white hover:bg-white/10 transition-colors cursor-pointer"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Pricing Summary */}
        <div className="bg-slate-950/70 px-6 py-3.5 border-b border-slate-800 flex items-center justify-between">
          <div>
            <div className="text-xs text-slate-400 font-medium">Exact Total Amount ({totalPages} Pages):</div>
            <div className="text-2xl font-black text-amber-400 flex items-center gap-2">
              <span>{formatETB(exactAmount)}</span>
              <button
                type="button"
                onClick={() => copyToClipboard(String(exactAmount), "amount")}
                className="text-xs text-amber-300 hover:text-amber-200 p-1 rounded hover:bg-slate-800"
                title="Copy Amount"
              >
                {copiedAmount ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5" />}
              </button>
            </div>
          </div>
          <div className="text-right text-xs text-slate-400">
            <div>Base (20 pgs): {formatETB(pricing.base_fee)}</div>
            {pricing.incremental_fee > 0 && (
              <div>Extra: +{formatETB(pricing.incremental_fee)}</div>
            )}
          </div>
        </div>

        {/* Body Content */}
        <div className="p-6 space-y-5">
          {/* Bank Account Details Card with Responsive Header */}
          <div className="p-4 rounded-2xl bg-slate-950 border border-slate-800 space-y-3 shadow-inner">
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-1.5 md:gap-2 text-xs text-purple-300">
              <span className="font-semibold flex items-center gap-1.5 text-slate-200">
                <Smartphone className="h-4 w-4 text-amber-400 flex-shrink-0" />
                <span>Commercial Bank of Ethiopia (CBE)</span>
              </span>
              <span className="text-amber-400 font-mono text-[11px] self-start md:self-auto bg-purple-950/70 px-2 py-0.5 rounded-md border border-purple-800/50">
                CBEBirr / Mobile Banking
              </span>
            </div>

            <div className="p-3 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-between">
              <div>
                <div className="text-[11px] text-slate-400">Account Number:</div>
                <div className="font-mono text-lg font-black tracking-wider text-amber-300">
                  {cbeAccNumber}
                </div>
              </div>
              <button
                type="button"
                onClick={() => copyToClipboard(cbeAccNumber, "account")}
                className="flex items-center gap-1 text-xs px-2.5 py-1.5 rounded-lg bg-amber-400 hover:bg-amber-300 text-purple-950 font-bold transition-all cursor-pointer"
              >
                {copiedAccount ? (
                  <>
                    <Check className="h-3.5 w-3.5" />
                    <span>Copied!</span>
                  </>
                ) : (
                  <>
                    <Copy className="h-3.5 w-3.5" />
                    <span>Copy Acc</span>
                  </>
                )}
              </button>
            </div>

            {/* Account Name with uppercase Tailwind class */}
            <div className="text-xs text-slate-300 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1 pt-1.5 border-t border-slate-800/80">
              <span className="text-slate-400">Account Name:</span>
              <span className="font-bold text-white uppercase tracking-wider">{cbeAccName}</span>
            </div>
          </div>

          {/* Transfer Instructions */}
          <div className="p-3 rounded-xl bg-amber-950/30 border border-amber-800/50 text-xs text-amber-200 space-y-1">
            <div className="font-bold flex items-center gap-1.5 text-amber-300">
              <Clock className="h-4 w-4 text-amber-400" />
              <span>How to pay & unlock instant download:</span>
            </div>
            <ol className="list-decimal list-inside space-y-0.5 text-[11px] text-amber-300/90">
              <li>Transfer <strong>{formatETB(exactAmount)}</strong> via CBE Mobile Banking or CBE Birr app.</li>
              <li>Copy the <strong>Transaction ID / Reference (FT number)</strong> from the SMS or slip.</li>
              <li>Paste the Transaction ID below to verify and unlock your full thesis instantly.</li>
            </ol>
          </div>

          {/* Transaction Submission Form with noValidate */}
          <form onSubmit={handleSubmitTxn} noValidate className="space-y-4">
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-slate-200 flex items-center justify-between">
                <span>Enter CBE Transaction ID / Reference (FT number)</span>
                <span className="text-rose-400">*</span>
              </label>
              <input
                type="text"
                disabled={isSubmitting || isPolling}
                placeholder="e.g. FT2609871234 or TXN987654"
                value={transactionRef}
                onChange={(e) => {
                  setTransactionRef(e.target.value.toUpperCase());
                  if (txnInputError) setTxnInputError(null);
                }}
                className={`w-full px-4 py-3 text-sm font-mono font-bold tracking-wide border-2 rounded-xl focus:outline-none uppercase bg-slate-950 text-slate-100 transition-colors ${
                  txnInputError
                    ? "border-rose-500 focus:border-rose-500 focus:ring-2 focus:ring-rose-500/20"
                    : "border-purple-800 focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20"
                }`}
              />

              {/* Custom UI Validation Message (No browser popup) */}
              {txnInputError && (
                <p className="text-xs text-rose-400 font-medium flex items-center gap-1.5 mt-1 animate-in fade-in-50">
                  <AlertCircle className="h-3.5 w-3.5 flex-shrink-0 text-rose-400" />
                  <span>{txnInputError}</span>
                </p>
              )}
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <label className="text-[11px] font-medium text-slate-400">Payer Name (Optional)</label>
                <input
                  type="text"
                  disabled={isSubmitting || isPolling}
                  placeholder="e.g. Abebe Bikila"
                  value={payerName}
                  onChange={(e) => setPayerName(e.target.value)}
                  className="w-full px-3 py-2 text-xs bg-slate-950 border border-slate-800 rounded-lg focus:outline-none focus:border-purple-500 text-slate-200"
                />
              </div>

              <div className="space-y-1">
                <label className="text-[11px] font-medium text-slate-400">Phone Number (Optional)</label>
                <input
                  type="tel"
                  disabled={isSubmitting || isPolling}
                  placeholder="0911223344"
                  value={payerPhone}
                  onChange={(e) => setPayerPhone(e.target.value)}
                  className="w-full px-3 py-2 text-xs bg-slate-950 border border-slate-800 rounded-lg focus:outline-none focus:border-purple-500 text-slate-200"
                />
              </div>
            </div>

            {errorMessage && (
              <div className="p-3 text-xs text-rose-300 bg-rose-950/50 rounded-xl border border-rose-900 flex items-center gap-2">
                <AlertCircle className="h-4 w-4 flex-shrink-0 text-rose-400" />
                <span>{errorMessage}</span>
              </div>
            )}

            {isPolling && (
              <div className="p-3 text-xs text-purple-200 bg-purple-950/40 rounded-xl border border-purple-800 flex items-center gap-2.5 animate-pulse">
                <Loader2 className="h-4 w-4 animate-spin text-purple-400 flex-shrink-0" />
                <div className="space-y-0.5">
                  <div className="font-bold text-purple-100">Awaiting CBE Webhook Confirmation...</div>
                  <div className="text-[11px] text-purple-300">Checking Transaction ID {transactionRef}</div>
                </div>
              </div>
            )}

            <div className="pt-1">
              <button
                type="submit"
                disabled={isSubmitting || isInitializing}
                className="w-full py-4 px-4 bg-gradient-to-r from-purple-700 via-indigo-800 to-purple-800 hover:from-purple-800 hover:to-indigo-900 text-white font-extrabold text-sm rounded-2xl shadow-xl shadow-purple-950/50 hover:scale-[1.01] active:scale-[0.99] transition-all flex items-center justify-center gap-2 disabled:opacity-60 cursor-pointer border border-purple-500/30"
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span>Submitting Reference...</span>
                  </>
                ) : isPolling ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span>Checking Status Live...</span>
                  </>
                ) : (
                  <>
                    <Lock className="h-4 w-4 text-amber-300" />
                    <span>Verify CBE Payment & Unlock .DOCX</span>
                    <ArrowRight className="h-4 w-4" />
                  </>
                )}
              </button>
            </div>
          </form>

          <div className="text-center text-[11px] text-slate-400 flex items-center justify-center gap-1.5">
            <ShieldCheck className="h-4 w-4 text-emerald-400" />
            <span>Automated CBE Email Webhook Engine • 24-Hour Supabase Storage Security</span>
          </div>
        </div>
      </div>
    </div>
  );
}
