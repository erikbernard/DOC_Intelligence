export interface CollectionLinkCreate {
  expires_hours?: number;
  max_uses?: number;
}

export interface CollectionLinkResponse {
  collection_link_id: string;
  persona_id: string;
  public_token: string;
  upload_url: string;
  expires_at: string;
  message: string;
}

export interface PublicTokenValidation {
  valid: boolean;
  persona_id: string;
  persona_name?: string;
  required_document_types: string[];
}
