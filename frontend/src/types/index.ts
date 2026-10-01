export interface MarginConfig {
  left_inches: number;
  top_inches: number;
  right_inches: number;
  bottom_inches: number;
}

export interface UniversityConfig {
  font_family: string;
  font_size_body: number;
  font_size_h1: number;
  font_size_h2: number;
  font_size_h3: number;
  line_spacing: number;
  paragraph_space_after: number;
  paragraph_space_before: number;
  first_line_indent_inches: number;
  margins: MarginConfig;
  alignment: string;
  toc_mode: string;
  page_numbering: {
    preliminary: string;
    main_body: string;
    position: string;
  };
}

export interface UniversityPreset {
  id: string;
  name_en: string;
  name_am: string;
  display_name: string;
  is_custom: boolean;
  config: UniversityConfig | null;
}

export interface CustomFormattingRules {
  font_family: "Times New Roman" | "Arial";
  font_size: 12 | 11;
  line_spacing: 1.5 | 2.0 | 1.0;
  margin_preset: "ethiopian_standard" | "equal_margins";
  toc_mode: "auto_generate" | "keep_existing";
}

export interface PricingDetail {
  base_fee: number;
  incremental_fee: number;
  total_fee: number;
  currency: string;
}

export interface PreviewResponse {
  status: "success" | "error";
  session_id: string;
  total_pages: number;
  preview_pages: string[]; // Base64 PNG data URLs
  pricing: PricingDetail;
  metadata: {
    filename: string;
    formatted_at: string;
    university: string;
    preset_id: string;
  };
  error_message?: string;
}

export interface PaymentInitiationResponse {
  status: "success" | "error";
  checkout_url: string;
  tx_ref: string;
  amount: number;
  currency: string;
  session_id: string;
}

export interface PaymentVerificationResponse {
  status: "paid" | "pending" | "failed";
  verified: boolean;
  download_url?: string;
  expires_in_hours?: number;
  file_name?: string;
  error?: string;
}
