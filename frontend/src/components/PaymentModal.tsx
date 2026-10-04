"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  X,
  Check,
  Copy,
  Lock,
  ArrowRight,
  Loader2,
  AlertCircle,
  Building,
  Smartphone,
  Clock,
  ShieldCheck,
  RefreshCw,
  HelpCircle,
} from "lucide-react";
import confetti from "canvas-confetti";
import {
  initiateCBEPayment,
  submitCBETransaction,
  checkTransactionStatus,
  fetchCBEDetails,
} from "@/lib/api";
import {
  PricingDetail,
  CBEPaymentInitiationResponse,
  TransactionStatusResponse,
} from "@/types";

interface PaymentModalProps {
  isOpen: boolean;
  onClose: () => void;
  sessionId: string;
  totalPages: number;
  pricing: PricingDetail;
  cbeAccountNumber?: string;
  cbeAccountName?: string;
  universityName: string;
  onPaymentSuccess: (statusData: TransactionStatusResponse) => void;
}

export function PaymentModal({
  isOpen,
  onClose,
  sessionId,
  totalPages,
  pricing,
  cbeAccountNumber,
  cbeAccountName,
  universityName,
  onPaymentSuccess,
}: PaymentModalProps) {
  const [initData, setInitData] = useState<CBEPaymentInitiationResponse | null>(null);
  const [isInitializing, setIsInitializing] = useState(false);

  // Form input states
  const [transactionRef, setTransactionRef] = useState("");
  const [payerName, setPayerName] = useState("");
  const [payerPhone, setPayerPhone] = useState("");

  // Submission & Polling states
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isPolling, setIsPolling] = useState(false);
  const [pollCount, setPollCount] = useState(0);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [txnInputError, setTxnInputError] = useState<string | null>(null);

  // Clipboard copy feedback
  const [copiedAccount, setCopiedAccount] = useState(false);
  const [copiedAmount, setCopiedAmount] = useState(false);

  const pollingTimerRef = useRef<NodeJS.Timeout | null>(null);

  const formatETB = (amount: number) => {
    return new Intl.NumberFormat("en-ET", {
      style: "currency",
      currency: "ETB",
      minimumFractionDigits: 2,
    }).format(amount);
  };

  // Initialize CBE payment metadata when modal opens
  useEffect(() => {
    if (!isOpen || !sessionId) return;

    let mounted = true;
    setIsInitializing(true);
    setErrorMessage(null);
    setTxnInputError(null);
    setPollCount(0);

    initiateCBEPayment(sessionId)
      .then((data) => {
        if (mounted) {
          setInitData(data);
          setIsInitializing(false);
        }
      })
      .catch(() => {
        if (mounted) {
          fetchCBEDetails().then((cbe) => {
            if (mounted) {
              setInitData({
                status: "pending",
                session_id: sessionId,
                amount_expected: pricing.total_fee,
                currency: pricing.currency || "ETB",
                total_pages: totalPages,
                cbe_account_number: cbeAccountNumber || cbe.cbe_account_number,
                cbe_account_name: cbeAccountName || cbe.cbe_account_name,
                pricing_breakdown: pricing,
                instructions: "Please transfer the exact amount to CBE and submit your Transaction ID.",
              });
              setIsInitializing(false);
            }
          });
        }
      });

    return () => {
      mounted = false;
      if (pollingTimerRef.current) clearInterval(pollingTimerRef.current);
    };
  }, [isOpen, sessionId, cbeAccountNumber, cbeAccountName, pricing, totalPages]);

  // Polling loop
  const startPollingStatus = () => {
    setIsPolling(true);
    setPollCount(0);

    if (pollingTimerRef.current) clearInterval(pollingTimerRef.current);

    pollingTimerRef.current = setInterval(async () => {
      try {
        setPollCount((prev) => prev + 1);
        const res = await checkTransactionStatus(sessionId);
        if (res.status === "approved" && res.verified) {
          if (pollingTimerRef.current) clearInterval(pollingTimerRef.current);
          setIsPolling(false);

          confetti({
            particleCount: 100,
            spread: 80,
            origin: { y: 0.6 },
          });

          await new Promise((r) => setTimeout(r, 600));
          onPaymentSuccess(res);
        } else if (res.status === "failed") {
          if (pollingTimerRef.current) clearInterval(pollingTimerRef.current);
          setIsPolling(false);
          setErrorMessage(res.message || "Payment verification failed. Please check the amount transferred.");
        }
      } catch {
        // Continue polling silently
      }
    }, 1800);
  };

  const handleManualRecheck = async () => {
    if (!sessionId) return;
    setIsSubmitting(true);
    try {
      const cleanRef = transactionRef.trim().toUpperCase();
      const res = await submitCBETransaction(
        sessionId,
        cleanRef || "CHECK",
        payerName.trim() || undefined,
        payerPhone.trim() || undefined
      );
      if (res.status === "approved" && res.download_url) {
        if (pollingTimerRef.current) clearInterval(pollingTimerRef.current);
        setIsPolling(false);
        setIsSubmitting(false);
        confetti({
          particleCount: 100,
          spread: 80,
          origin: { y: 0.6 },
        });
        onPaymentSuccess({
          status: "approved",
          session_id: sessionId,
          transaction_ref: cleanRef,
          amount_expected: res.amount_expected,
          verified: true,
          download_url: res.download_url,
          file_name: res.file_name,
        });
      } else {
        const statusRes = await checkTransactionStatus(sessionId);
        setIsSubmitting(false);
        if (statusRes.status === "approved" && statusRes.verified) {
          if (pollingTimerRef.current) clearInterval(pollingTimerRef.current);
          setIsPolling(false);
          confetti({
            particleCount: 100,
            spread: 80,
            origin: { y: 0.6 },
          });
          onPaymentSuccess(statusRes);
        }
      }
    } catch {
      setIsSubmitting(false);
    }
  };

  const handleSubmitTxn = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setErrorMessage(null);

    if (!transactionRef || !transactionRef.trim()) {
      setTxnInputError("Please enter your Transaction ID (e.g. FT... or 10-digit code).");
      return;
    }

    setTxnInputError(null);
    setIsSubmitting(true);

    try {
      const cleanRef = transactionRef.trim().toUpperCase();
      const res = await submitCBETransaction(
        sessionId,
        cleanRef,
        payerName.trim() || undefined,
        payerPhone.trim() || undefined
      );

      setIsSubmitting(false);

      if (res.status === "approved" && res.download_url) {
        if (pollingTimerRef.current) clearInterval(pollingTimerRef.current);
        setIsPolling(false);
        confetti({
          particleCount: 100,
          spread: 80,
          origin: { y: 0.6 },
        });
        onPaymentSuccess({
          status: "approved",
          session_id: sessionId,
          transaction_ref: cleanRef,
          amount_expected: res.amount_expected,
          verified: true,
          download_url: res.download_url,
          file_name: res.file_name,
        });
      } else {
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

  const cbeAccNumber = initData?.cbe_account_number || cbeAccountNumber || "1000659424936";
  const cbeAccName = initData?.cbe_account_name || cbeAccountName || "BINIAM KEBEDE AMADE";
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
            disabled={isSubmitting}
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

            {/* Account Name */}
            <div className="text-xs text-slate-300 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1 pt-1.5 border-t border-slate-800/80">
              <span className="text-slate-400">Account Name:</span>
              <span className="font-bold text-white uppercase tracking-wider">{cbeAccName}</span>
            </div>
          </div>

          {/* Transfer Instructions */}
          <div className="p-3.5 rounded-xl bg-amber-950/30 border border-amber-800/50 text-xs text-amber-200 space-y-1.5">
            <div className="font-bold flex items-center gap-1.5 text-amber-300">
              <Clock className="h-4 w-4 text-amber-400" />
              <span>How to pay & unlock instant download:</span>
            </div>
            <ol className="list-decimal list-inside space-y-1 text-[11px] text-amber-200/90 leading-relaxed">
              <li>Transfer <strong>{formatETB(exactAmount)}</strong> via CBE Mobile Banking, CBE Birr, or COOPay app to account <strong>{cbeAccNumber}</strong>.</li>
              <li>Copy the <strong>Transaction ID / Reference (FT number or 10-digit number)</strong> from the SMS or slip.</li>
              <li>Paste the Transaction ID below to verify and unlock your full thesis instantly.</li>
            </ol>
          </div>

          {/* Transaction Submission Form */}
          <form onSubmit={handleSubmitTxn} noValidate className="space-y-4">
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-slate-200 flex items-center justify-between">
                <span>Enter CBE Transaction ID / Reference (FT number)</span>
                <span className="text-rose-400">*</span>
              </label>
              <input
                type="text"
                disabled={isSubmitting}
                placeholder="e.g. 2798853639 or FT2609871234"
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
                  disabled={isSubmitting}
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
                  disabled={isSubmitting}
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
              <div className="p-3.5 text-xs text-purple-200 bg-purple-950/40 rounded-xl border border-purple-800/80 space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <Loader2 className="h-4 w-4 animate-spin text-purple-400 flex-shrink-0" />
                    <div>
                      <div className="font-bold text-purple-100">Verifying with CBE Server...</div>
                      <div className="text-[11px] text-purple-300 font-mono">Txn ID: {transactionRef}</div>
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={handleManualRecheck}
                    className="flex items-center gap-1 text-[11px] px-2.5 py-1 bg-purple-900/60 hover:bg-purple-800 text-purple-200 rounded-lg border border-purple-700/60 transition-colors cursor-pointer"
                  >
                    <RefreshCw className="h-3 w-3" />
                    <span>Re-check</span>
                  </button>
                </div>
                {pollCount > 3 && (
                  <div className="text-[11px] text-amber-300/90 bg-amber-950/40 p-2 rounded-lg border border-amber-900/40 flex items-start gap-1.5">
                    <HelpCircle className="h-3.5 w-3.5 text-amber-400 flex-shrink-0 mt-0.5" />
                    <span>
                      Please ensure the transfer was completed in your banking app. If your transfer was just sent, it takes a few moments for the bank notification to arrive.
                    </span>
                  </div>
                )}
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
                    <span>Verifying with CBE...</span>
                  </>
                ) : isPolling ? (
                  <>
                    <RefreshCw className="h-4 w-4" />
                    <span>Re-check Status Live...</span>
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
