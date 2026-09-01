import { Injectable, computed, inject, signal } from '@angular/core';
import { environment } from '../../../environments/environment';
import { NotificationItem, NotificationType } from '../models/notification.model';
import { AuthService } from './auth.service';
import { ToastService } from './toast.service';

@Injectable({
  providedIn: 'root',
})
export class NotificationService {
  private authService = inject(AuthService);
  private toastService = inject(ToastService);

  private eventSource: EventSource | null = null;
  private _notifications = signal<NotificationItem[]>([]);
  private _connected = signal<boolean>(false);
  private _latestEvent = signal<{ event: string; payload: any } | null>(null);

  public readonly notifications = this._notifications.asReadonly();
  public readonly isConnected = this._connected.asReadonly();
  public readonly latestEvent = this._latestEvent.asReadonly();
  public readonly unreadCount = computed(() => this._notifications().filter((n) => !n.read).length);

  constructor() {
    // Automatically connect/disconnect based on authentication
    if (this.authService.isAuthenticated()) {
      this.connect();
    }
  }

  public connect(): void {
    const token = this.authService.token();
    if (!token || this.eventSource) return;

    const sseUrl = `${environment.sseUrl}?token=${encodeURIComponent(token)}`;
    this.eventSource = new EventSource(sseUrl);

    this.eventSource.onopen = () => {
      this._connected.set(true);
    };

    this.eventSource.onerror = () => {
      this._connected.set(false);
      this.disconnect();
      // Reconnect after 5 seconds if authenticated
      if (this.authService.isAuthenticated()) {
        setTimeout(() => this.connect(), 5000);
      }
    };

    // Listen to all relevant backend domain events
    const handledEvents = [
      'document.processing',
      'document.ready',
      'document.needs_review',
      'document.rejected',
      'persona.completed',
    ];

    handledEvents.forEach((eventName) => {
      this.eventSource?.addEventListener(eventName, (e: MessageEvent) => {
        try {
          const payload = JSON.parse(e.data);
          this.handleIncomingEvent(eventName, payload);
        } catch {
          // ignore malformed payloads
        }
      });
    });
  }

  public disconnect(): void {
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
      this._connected.set(false);
    }
  }

  public markAllAsRead(): void {
    this._notifications.update((current) =>
      current.map((item) => ({ ...item, read: true }))
    );
  }

  public markAsRead(id: string): void {
    this._notifications.update((current) =>
      current.map((item) => (item.id === id ? { ...item, read: true } : item))
    );
  }

  public clearAll(): void {
    this._notifications.set([]);
  }

  private handleIncomingEvent(eventName: string, payload: any): void {
    this._latestEvent.set({ event: eventName, payload });

    let title = 'Notificação';
    let message = 'Novo evento recebido.';
    let type: NotificationType = 'info';
    let link: string | undefined = undefined;

    switch (eventName) {
      case 'document.processing':
        title = 'Processando OCR';
        message = `O documento está sendo analisado pelos motores de inteligência.`;
        type = 'info';
        break;

      case 'document.ready':
        title = 'Documento Aprovado!';
        message = `Documento validado com sucesso (READY).`;
        type = 'success';
        if (payload.persona_id) {
          link = `/personas/${payload.persona_id}`;
        }
        this.toastService.success(message);
        break;

      case 'document.needs_review':
        title = 'Revisão Necessária (RN-01/02)';
        message = `Documento requer conferência visual do operador.`;
        type = 'warning';
        if (payload.document_id) {
          link = `/documents/${payload.document_id}/review`;
        }
        this.toastService.warning(message);
        break;

      case 'document.rejected':
        title = 'Documento Rejeitado';
        message = `Documento ilegível/rejeitado (RN-09).`;
        type = 'error';
        this.toastService.error(message);
        break;

      case 'persona.completed':
        title = 'Onboarding Concluído! (RN-15)';
        message = `Todos os documentos da Persona '${payload.name || 'titular'}' foram validados com sucesso!`;
        type = 'success';
        if (payload.persona_id) {
          link = `/personas/${payload.persona_id}`;
        }
        this.toastService.success(message, 8000);
        break;
    }

    const notification: NotificationItem = {
      id: Math.random().toString(36).substring(2, 9),
      title,
      message,
      timestamp: new Date(),
      read: false,
      type,
      link,
      documentId: payload.document_id,
      personaId: payload.persona_id,
    };

    this._notifications.update((current) => [notification, ...current.slice(0, 49)]);
  }
}
