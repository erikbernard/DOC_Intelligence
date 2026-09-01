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
      'document.uploaded',
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

    const personaName =
      payload.persona_name ||
      payload.name ||
      payload.extracted_data?.fields?.nome?.value ||
      payload.extracted_data?.fields?.nome ||
      '';

    let title = 'Notificação';
    let message = 'Novo evento recebido.';
    let type: NotificationType = 'info';
    const docId = payload.document_id || payload.documentId;
    const personaId = payload.persona_id || payload.personaId;
    let link: string | undefined = docId
      ? `/documents/${docId}/review`
      : personaId
        ? `/personas/${personaId}`
        : undefined;

    switch (eventName) {
      case 'document.uploaded':
        title = 'Documento Recebido';
        message = personaName
          ? `Novo documento enviado para ${personaName}.`
          : 'Novo documento enviado pelo link de coleta.';
        type = 'info';
        if (docId) {
          link = `/documents/${docId}/review`;
        }
        this.toastService.info(message);
        break;

      case 'document.processing':
        title = 'Processando OCR';
        message = personaName
          ? `O documento de ${personaName} está sendo processado pelos motores de IA.`
          : 'O documento está sendo processado pelos motores de IA.';
        type = 'info';
        if (docId) {
          link = `/documents/${docId}/review`;
        }
        // Notificação silenciosa: não dispara toast intrusivo na tela
        break;

      case 'document.ready':
        title = 'Documento Aprovado!';
        message = personaName
          ? `Documento de ${personaName} validado com sucesso (READY).`
          : 'Documento validado com sucesso (READY).';
        type = 'success';
        if (docId) {
          link = `/documents/${docId}/review`;
        } else if (personaId) {
          link = `/personas/${personaId}`;
        }
        this.toastService.success(message);
        break;

      case 'document.needs_review':
        title = 'Revisão Necessária (RN-01/02)';
        message = personaName
          ? `Documento de ${personaName} requer conferência visual do operador.`
          : 'Documento requer conferência visual do operador.';
        type = 'warning';
        if (docId) {
          link = `/documents/${docId}/review`;
        } else if (personaId) {
          link = `/personas/${personaId}`;
        }
        this.toastService.warning(message);
        break;

      case 'document.rejected':
        title = 'Documento Rejeitado';
        message = personaName
          ? `Documento de ${personaName} foi rejeitado (RN-09).`
          : 'Documento ilegível/rejeitado (RN-09).';
        type = 'error';
        if (docId) {
          link = `/documents/${docId}/review`;
        } else if (personaId) {
          link = `/personas/${personaId}`;
        }
        this.toastService.error(message);
        break;

      case 'persona.completed':
        title = 'Onboarding Concluído! (RN-15)';
        message = personaName
          ? `Todos os documentos de ${personaName} foram validados com sucesso!`
          : 'Todos os documentos da Persona foram validados com sucesso!';
        type = 'success';
        if (personaId) {
          link = `/personas/${personaId}`;
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
      documentId: docId,
      personaId: personaId,
    };

    this._notifications.update((current) => [notification, ...current.slice(0, 49)]);
  }
}
