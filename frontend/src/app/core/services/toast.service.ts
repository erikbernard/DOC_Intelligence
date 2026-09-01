import { Injectable, signal } from '@angular/core';
import { ToastItem, NotificationType } from '../models/notification.model';

@Injectable({
  providedIn: 'root',
})
export class ToastService {
  private _toasts = signal<ToastItem[]>([]);
  public readonly toasts = this._toasts.asReadonly();

  public show(message: string, type: NotificationType = 'info', durationMs: number = 4000): void {
    const id = Math.random().toString(36).substring(2, 9);
    const toast: ToastItem = { id, message, type, durationMs };

    this._toasts.update((current) => [...current, toast]);

    if (durationMs > 0) {
      setTimeout(() => {
        this.remove(id);
      }, durationMs);
    }
  }

  public success(message: string, durationMs: number = 4000): void {
    this.show(message, 'success', durationMs);
  }

  public error(message: string, durationMs: number = 6000): void {
    this.show(message, 'error', durationMs);
  }

  public warning(message: string, durationMs: number = 5000): void {
    this.show(message, 'warning', durationMs);
  }

  public info(message: string, durationMs: number = 4000): void {
    this.show(message, 'info', durationMs);
  }

  public remove(id: string): void {
    this._toasts.update((current) => current.filter((t) => t.id !== id));
  }
}
