import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { Persona, PersonaCreate, PersonaFilterParams } from '../models/persona.model';
import { CollectionLinkCreate, CollectionLinkResponse } from '../models/collection-link.model';

@Injectable({
  providedIn: 'root',
})
export class PersonaService {
  private http = inject(HttpClient);
  private baseUrl = `${environment.apiUrl}/personas`;

  public list(params?: PersonaFilterParams): Observable<Persona[]> {
    let httpParams = new HttpParams();
    if (params?.status) {
      httpParams = httpParams.set('status', params.status);
    }
    if (params?.search) {
      httpParams = httpParams.set('search', params.search);
    }
    if (params?.skip !== undefined) {
      httpParams = httpParams.set('skip', params.skip.toString());
    }
    if (params?.limit !== undefined) {
      httpParams = httpParams.set('limit', params.limit.toString());
    }

    return this.http.get<Persona[]>(this.baseUrl, { params: httpParams });
  }

  public get(id: string): Observable<Persona> {
    return this.http.get<Persona>(`${this.baseUrl}/${id}`);
  }

  public create(data: PersonaCreate): Observable<Persona> {
    return this.http.post<Persona>(this.baseUrl, data);
  }

  public delete(id: string): Observable<{ message: string }> {
    return this.http.delete<{ message: string }>(`${this.baseUrl}/${id}`);
  }

  public createCollectionLink(
    personaId: string,
    data: CollectionLinkCreate = {}
  ): Observable<CollectionLinkResponse> {
    const payload = {
      persona_id: personaId,
      expires_hours: data.expires_hours || 48,
      max_uses: data.max_uses || 5,
    };
    return this.http.post<CollectionLinkResponse>(
      `${environment.apiUrl}/collection-links/`,
      payload
    );
  }
}
