import { PreviewResponse, PaymentInitiationResponse, PaymentVerificationResponse, CustomFormattingRules } from "@/types";

const API_BASE = "/api/backend";

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

export async function initiatePayment(
  sessionId: string,
  studentInfo: { email: string; firstName: string; lastName: string; phoneNumber?: string }
): Promise<PaymentInitiationResponse> {
  const response = await fetch(`${API_BASE}/initiate-payment`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      session_id: sessionId,
      email: studentInfo.email,
      first_name: studentInfo.firstName,
      last_name: studentInfo.lastName,
      phone_number: studentInfo.phoneNumber,
    }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Payment initiation failed (${response.status}).`);
  }

  return response.json();
}

export async function verifyPayment(
  sessionId: string,
  txRef: string
): Promise<PaymentVerificationResponse> {
  const response = await fetch(`${API_BASE}/verify-payment`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      session_id: sessionId,
      tx_ref: txRef,
    }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Payment verification failed (${response.status}).`);
  }

  return response.json();
}

export function getDownloadUrl(sessionId: string): string {
  return `${API_BASE}/download/${sessionId}`;
}
