export type NotificationType = 'info' | 'success' | 'warning' | 'error';

export interface NotificationItem {
  id: string;
  title: string;
  message: string;
  timestamp: Date;
  read: boolean;
  type: NotificationType;
  link?: string;
  documentId?: string;
  personaId?: string;
}

export interface ToastItem {
  id: string;
  message: string;
  type: NotificationType;
  durationMs?: number;
}
