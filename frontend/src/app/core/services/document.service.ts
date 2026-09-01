import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import {
  DocumentDetailRead,
  DocumentLockResponse,
  DocumentRead,
  DocumentRejectRequest,
  DocumentReviewUpdate,
  DocumentStatus,
} from '../models/document.model';

@Injectable({
  providedIn: 'root',
})
export class DocumentService {
  private http = inject(HttpClient);
  private baseUrl = `${environment.apiUrl}/documents`;

  public list(options?: {
    personaId?: string;
    templateId?: string;
    status?: DocumentStatus;
    inReview?: boolean;
  }): Observable<DocumentRead[]> {
    let params = new HttpParams();
    if (options?.personaId) params = params.set('persona_id', options.personaId);
    if (options?.templateId) params = params.set('template_id', options.templateId);
    if (options?.status) params = params.set('status_filter', options.status);
    if (options?.inReview !== undefined) params = params.set('in_review', options.inReview.toString());

    return this.http.get<DocumentRead[]>(`${this.baseUrl}/`, { params });
  }

  public get(documentId: string): Observable<DocumentDetailRead> {
    return this.http.get<DocumentDetailRead>(`${this.baseUrl}/${documentId}`);
  }

  public lock(documentId: string): Observable<DocumentLockResponse> {
    return this.http.post<DocumentLockResponse>(`${this.baseUrl}/${documentId}/lock`, {});
  }

  public unlock(documentId: string): Observable<{ message: string }> {
    return this.http.post<{ message: string }>(`${this.baseUrl}/${documentId}/unlock`, {});
  }

  public review(documentId: string, payload: DocumentReviewUpdate): Observable<DocumentDetailRead> {
    return this.http.put<DocumentDetailRead>(`${this.baseUrl}/${documentId}/review`, payload);
  }

  public reject(documentId: string, payload: DocumentRejectRequest): Observable<DocumentDetailRead> {
    return this.http.post<DocumentDetailRead>(`${this.baseUrl}/${documentId}/reject`, payload);
  }

  public uploadInternal(
    personaId: string,
    file: File,
    documentType: string = 'CIN'
  ): Observable<{ message: string; document_id: string }> {
    const formData = new FormData();
    formData.append('file', file, file.name);
    formData.append('persona_id', personaId);
    formData.append('document_type', documentType);

    return this.http.post<{ message: string; document_id: string }>(
      `${this.baseUrl}/upload`,
      formData
    );
  }

  public uploadPublic(
    token: string,
    file: File,
    documentType: string = 'CIN'
  ): Observable<{ message: string; document_id: string; status: string; persona_id: string }> {
    const formData = new FormData();
    formData.append('file', file, file.name);
    formData.append('document_type', documentType);

    return this.http.post<{
      message: string;
      document_id: string;
      status: string;
      persona_id: string;
    }>(`${environment.apiUrl}/public/upload?token=${encodeURIComponent(token)}`, formData);
  }
}
