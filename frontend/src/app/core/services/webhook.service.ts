import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { WebhookConfig, WebhookCreate, WebhookDeliveryLog } from '../models/webhook.model';

@Injectable({
  providedIn: 'root',
})
export class WebhookService {
  private http = inject(HttpClient);
  private baseUrl = `${environment.apiUrl}/webhooks`;

  public list(): Observable<WebhookConfig[]> {
    return this.http.get<WebhookConfig[]>(`${this.baseUrl}/`);
  }

  public create(data: WebhookCreate): Observable<WebhookConfig> {
    return this.http.post<WebhookConfig>(`${this.baseUrl}/`, data);
  }

  public delete(id: string): Observable<{ message: string }> {
    return this.http.delete<{ message: string }>(`${this.baseUrl}/${id}`);
  }

  public getLogs(webhookId: string): Observable<WebhookDeliveryLog[]> {
    return this.http.get<WebhookDeliveryLog[]>(`${this.baseUrl}/${webhookId}/logs`);
  }
}
