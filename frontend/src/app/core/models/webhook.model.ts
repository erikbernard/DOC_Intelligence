export interface WebhookConfig {
  id: string;
  target_url: string;
  secret_token?: string | null;
  events: string[];
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface WebhookCreate {
  target_url: string;
  secret_token?: string;
  events: string[];
  is_active?: boolean;
}

export interface WebhookDeliveryLog {
  id: string;
  webhook_id: string;
  event_name: string;
  status_code: number;
  success: boolean;
  response_body?: string | null;
  attempt_count: number;
  created_at: string;
}
