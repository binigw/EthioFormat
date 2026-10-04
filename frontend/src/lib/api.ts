import {
  PreviewResponse,
  CBEPaymentInitiationResponse,
  SubmitCBETxnResponse,
  TransactionStatusResponse,
  CustomFormattingRules,
} from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "https://ethioformat.onrender.com/api";

export async function uploadAndPreviewThesis(
  file: File,
  presetId: string,
  customRules?: CustomFormattingRules
): Promise<PreviewResponse> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("preset_id", presetId);

  if (presetId === "custom" && customRules) {
    formData.append("custom_rules", JSON.stringify(customRules));
  }

  const response = await fetch(`${API_BASE}/preview`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Server error (${response.status}) while processing document.`);
  }

  return response.json();
}

/**
 * Fetches official CBE Account details from backend.
 */
export async function fetchCBEDetails(): Promise<{ cbe_account_number: string; cbe_account_name: string }> {
  try {
    const response = await fetch(`${API_BASE}/cbe-details`);
    if (response.ok) {
      return response.json();
    }
  } catch {}
  return {
    cbe_account_number: "1000659424936",
    cbe_account_name: "BINIAM KEBEDE AMADE",
  };
}

/**
 * Initiates CBE Birr Payment, returns CBE account details and expected amount.
 */
export async function initiateCBEPayment(
  sessionId: string,
  studentInfo?: { name?: string; email?: string; phone?: string }
): Promise<CBEPaymentInitiationResponse> {
  const response = await fetch(`${API_BASE}/initiate-cbe-payment`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      session_id: sessionId,
      student_name: studentInfo?.name,
      student_email: studentInfo?.email,
      student_phone: studentInfo?.phone,
    }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `CBE Payment initiation failed (${response.status}).`);
  }

  return response.json();
}

/**
 * Submits the CBE Transaction ID (FT/TXN reference) entered by user.
 */
export async function submitCBETransaction(
  sessionId: string,
  transactionRef: string,
  payerName?: string,
  payerPhone?: string
): Promise<SubmitCBETxnResponse> {
  const response = await fetch(`${API_BASE}/payment/submit-cbe-txn`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      session_id: sessionId,
      transaction_ref: transactionRef,
      payer_name: payerName,
      payer_phone: payerPhone,
    }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Transaction submission failed (${response.status}).`);
  }

  return response.json();
}

/**
 * Polls backend / Supabase for transaction approval status.
 */
export async function checkTransactionStatus(
  sessionId: string
): Promise<TransactionStatusResponse> {
  const response = await fetch(`${API_BASE}/payment/status/${sessionId}`, {
    method: "GET",
    headers: {
      "Cache-Control": "no-cache",
    },
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Status check failed (${response.status}).`);
  }

  return response.json();
}

export function getDownloadUrl(sessionId: string): string {
  return `${API_BASE}/download/${sessionId}`;
}
