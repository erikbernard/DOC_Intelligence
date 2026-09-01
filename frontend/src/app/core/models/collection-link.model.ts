export interface CollectionLinkCreate {
  expires_hours?: number;
  max_uses?: number;
}

export interface CollectionLinkResponse {
  id: string;
  persona_id: string;
  token: string;
  public_token?: string;
  public_url?: string;
  upload_url?: string;
  expires_at: string;
  max_uses?: number;
  uses_count?: number;
  is_active?: boolean;
  is_expired?: boolean;
  message?: string;
}

export interface PublicTokenValidation {
  valid: boolean;
  persona_id: string;
  persona_name?: string;
  required_document_types: string[];
}
