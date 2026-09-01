export type DocumentStatus =
  | 'PENDING'
  | 'PROCESSING'
  | 'READY'
  | 'NEEDS_REVIEW'
  | 'REJECTED'
  | 'FAILED';

export type UploadOrigin = 'INTERNAL_APP' | 'PUBLIC_LINK' | 'SYSTEM_USER';

export interface ExtractedFieldDetail {
  value: string | null;
  raw_value?: string | null;
  confidence: number;
  is_valid: boolean;
  is_fuzzy_corrected?: boolean;
  warning?: string | null;
}

export interface ExtractedData {
  document_type?: string;
  template_code?: string;
  fields: Record<string, ExtractedFieldDetail>;
  validation_errors: string[];
  is_auto_approved?: boolean;
  is_manually_approved?: boolean;
  manual_review_notes?: string | null;
}

export interface DocumentRead {
  id: string;
  persona_id: string;
  template_id?: string | null;
  raw_file_name: string;
  sanitized_file_name: string;
  mime_type: string;
  file_size_bytes: int;
  status: DocumentStatus;
  confidence_score?: number | null;
  locked_by_user_id?: string | null;
  locked_by_user_name?: string | null;
  locked_at?: string | null;
  lock_expires_at?: string | null;
  upload_origin: UploadOrigin;
  created_at: string;
  updated_at: string;
  preview_url?: string | null;
}

export type int = number;

export interface DocumentDetailRead extends DocumentRead {
  storage_path: string;
  extracted_data: ExtractedData;
  raw_ocr_data: Record<string, any>;
  failure_reason?: string | null;
  rejection_reason?: string | null;
  created_by_user_id?: string | null;
  approved_by_user_id?: string | null;
  approved_at?: string | null;
}

export interface DocumentReviewUpdate {
  template_code?: string;
  template_id?: string;
  document_type?: string;
  corrected_data: Record<string, any>;
  notes?: string;
}

export interface DocumentRejectRequest {
  rejection_reason: string;
}

export interface DocumentLockResponse {
  document_id: string;
  locked: boolean;
  locked_by_user_id?: string | null;
  locked_by_user_name?: string | null;
  locked_at?: string | null;
  lock_expires_at?: string | null;
  message: string;
}
