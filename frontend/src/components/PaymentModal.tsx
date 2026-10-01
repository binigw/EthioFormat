"use client";

import React, { useState } from "react";
import { formatETB } from "@/lib/utils";
import { PricingDetail, PaymentVerificationResponse } from "@/types";
import { initiatePayment, verifyPayment } from "@/lib/api";
import {
  X,
  CreditCard,
  Smartphone,
  ShieldCheck,
  CheckCircle2,
  Loader2,
  ArrowRight,
  ExternalLink,
  Lock,
  Sparkles,
} from "lucide-react";
import confetti from "canvas-confetti";

interface PaymentModalProps {
  isOpen: boolean;
  onClose: () => void;
  sessionId: string;
  totalPages: number;
  pricing: PricingDetail;
  universityName: string;
  onPaymentSuccess: (data: PaymentVerificationResponse) => void;
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
  const [firstName, setFirstName] = useState("Abebe");
  const [lastName, setLastName] = useState("Bikila");
  const [email, setEmail] = useState("student@aau.edu.et");
  const [phoneNumber, setPhoneNumber] = useState("0911223344");
  const [paymentMethod, setPaymentMethod] = useState<"telebirr" | "cbebirr" | "chapa">("telebirr");

  const [isLoading, setIsLoading] = useState(false);
  const [statusMessage, setStatusMessage] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleProcessPayment = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setIsLoading(true);
    setStatusMessage("Connecting to Chapa Payment Gateway...");

    try {
      // 1. Initiate transaction
      const initRes = await initiatePayment(sessionId, {
        firstName,
        lastName,
        email,
        phoneNumber,
      });

      setStatusMessage("Processing transaction with Telebirr / Chapa...");
      await new Promise((r) => setTimeout(r, 1200));

      // 2. Verify payment
      setStatusMessage("Verifying payment security signature...");
      const verifyRes = await verifyPayment(sessionId, initRes.tx_ref);

      if (verifyRes.verified) {
        // Trigger celebratory confetti
        confetti({
          particleCount: 80,
          spread: 70,
          origin: { y: 0.6 },
        });

        setStatusMessage("Payment Verified! Unlocking full formatted thesis...");
        await new Promise((r) => setTimeout(r, 800));

        onPaymentSuccess(verifyRes);
      } else {
        setErrorMessage(verifyRes.error || "Payment verification failed. Please try again.");
      }
    } catch (err: any) {
      setErrorMessage(err.message || "An error occurred during payment processing.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/70 backdrop-blur-sm animate-in fade-in-50 duration-200">
      <div className="relative w-full max-w-lg bg-white rounded-2xl shadow-2xl border border-slate-200 overflow-hidden">
        {/* Modal Header */}
        <div className="bg-gradient-to-r from-emerald-700 via-emerald-600 to-teal-700 px-6 py-5 text-white flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-white/10 backdrop-blur-md">
              <ShieldCheck className="h-5 w-5 text-emerald-200" />
            </div>
            <div>
              <h3 className="font-bold text-lg leading-tight">Chapa Secure Checkout</h3>
              <p className="text-xs text-emerald-100">{universityName}</p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            disabled={isLoading}
            className="p-1.5 rounded-lg text-white/80 hover:text-white hover:bg-white/10 transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Amount Summary */}
        <div className="bg-slate-50 px-6 py-4 border-b border-slate-200 flex items-center justify-between">
          <div>
            <div className="text-xs text-slate-500 font-medium">Total Amount ({totalPages} Pages):</div>
            <div className="text-2xl font-black text-slate-900">{formatETB(pricing.total_fee)}</div>
          </div>
          <div className="text-right text-xs text-slate-500">
            <div>Base (20 pgs): {formatETB(pricing.base_fee)}</div>
            {pricing.incremental_fee > 0 && (
              <div>Extra: +{formatETB(pricing.incremental_fee)}</div>
            )}
          </div>
        </div>

        {/* Checkout Form */}
        <form onSubmit={handleProcessPayment} className="p-6 space-y-4">
          {/* Payment Method Selector */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-700">Choose Payment Method</label>
            <div className="grid grid-cols-3 gap-2">
              <button
                type="button"
                onClick={() => setPaymentMethod("telebirr")}
                className={`p-3 rounded-xl border text-center transition-all ${
                  paymentMethod === "telebirr"
                    ? "border-emerald-600 bg-emerald-50/70 text-emerald-950 font-bold shadow-sm"
                    : "border-slate-200 hover:border-slate-300 text-slate-700"
                }`}
              >
                <Smartphone className="h-5 w-5 mx-auto mb-1 text-emerald-600" />
                <div className="text-xs">Telebirr</div>
              </button>

              <button
                type="button"
                onClick={() => setPaymentMethod("cbebirr")}
                className={`p-3 rounded-xl border text-center transition-all ${
                  paymentMethod === "cbebirr"
                    ? "border-emerald-600 bg-emerald-50/70 text-emerald-950 font-bold shadow-sm"
                    : "border-slate-200 hover:border-slate-300 text-slate-700"
                }`}
              >
                <Smartphone className="h-5 w-5 mx-auto mb-1 text-purple-600" />
                <div className="text-xs">CBE Birr</div>
              </button>

              <button
                type="button"
                onClick={() => setPaymentMethod("chapa")}
                className={`p-3 rounded-xl border text-center transition-all ${
                  paymentMethod === "chapa"
                    ? "border-emerald-600 bg-emerald-50/70 text-emerald-950 font-bold shadow-sm"
                    : "border-slate-200 hover:border-slate-300 text-slate-700"
                }`}
              >
                <CreditCard className="h-5 w-5 mx-auto mb-1 text-blue-600" />
                <div className="text-xs">Cards / Chapa</div>
              </button>
            </div>
          </div>

          {/* Student Contact Info */}
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <label className="text-xs font-medium text-slate-700">First Name</label>
              <input
                type="text"
                required
                value={firstName}
                onChange={(e) => setFirstName(e.target.value)}
                className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:border-emerald-500"
              />
            </div>
            <div className="space-y-1">
              <label className="text-xs font-medium text-slate-700">Last Name</label>
              <input
                type="text"
                required
                value={lastName}
                onChange={(e) => setLastName(e.target.value)}
                className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:border-emerald-500"
              />
            </div>
          </div>

          <div className="space-y-1">
            <label className="text-xs font-medium text-slate-700">Student Email Address</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:border-emerald-500"
            />
          </div>

          <div className="space-y-1">
            <label className="text-xs font-medium text-slate-700">Phone Number (Telebirr / CBE)</label>
            <input
              type="tel"
              required
              value={phoneNumber}
              onChange={(e) => setPhoneNumber(e.target.value)}
              className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:border-emerald-500"
            />
          </div>

          {errorMessage && (
            <div className="p-3 text-xs text-rose-700 bg-rose-50 rounded-lg border border-rose-200">
              {errorMessage}
            </div>
          )}

          {isLoading && (
            <div className="p-3 text-xs text-emerald-800 bg-emerald-50 rounded-lg border border-emerald-200 flex items-center gap-2">
              <Loader2 className="h-4 w-4 animate-spin text-emerald-600" />
              <span>{statusMessage}</span>
            </div>
          )}

          <div className="pt-2">
            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-3.5 px-4 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-xl shadow-lg shadow-emerald-600/30 transition-all flex items-center justify-center gap-2 disabled:opacity-60 cursor-pointer"
            >
              {isLoading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span>Processing Payment...</span>
                </>
              ) : (
                <>
                  <Lock className="h-4 w-4" />
                  <span>Pay {formatETB(pricing.total_fee)} & Download .DOCX</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
