import { Component, OnInit, effect, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterModule } from '@angular/router';
import { PersonaService } from '../../../core/services/persona.service';
import { DocumentService } from '../../../core/services/document.service';
import { NotificationService } from '../../../core/services/notification.service';
import { ToastService } from '../../../core/services/toast.service';
import { Persona } from '../../../core/models/persona.model';
import { DocumentRead } from '../../../core/models/document.model';
import { CollectionLinkResponse } from '../../../core/models/collection-link.model';

@Component({
  selector: 'app-persona-detail',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  template: `
    <div class="space-y-6">
      <!-- Breadcrumb & Back -->
      <div class="flex items-center space-x-2 text-xs text-base-content/60">
        <a routerLink="/personas" class="link link-hover">Personas</a>
        <span>/</span>
        <span class="font-semibold text-base-content">{{ persona()?.name || 'Detalhes' }}</span>
      </div>

      @if (loadingPersona()) {
        <div class="p-12 text-center">
          <span class="loading loading-spinner loading-lg text-primary"></span>
        </div>
      } @else if (persona()) {
        <!-- Persona Header Info Card -->
        <div class="card bg-base-100 border border-base-200 shadow-xs">
          <div class="card-body p-6">
            <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div>
                <div class="flex items-center space-x-3">
                  <h1 class="text-2xl font-bold text-base-content">{{ persona()?.name }}</h1>
                  @switch (persona()?.status) {
                    @case ('ONBOARDING_COMPLETED') {
                      <span class="badge badge-success gap-1 font-semibold text-xs">
                        <span class="w-1.5 h-1.5 rounded-full bg-success-content"></span>
                        Onboarding Completo (RN-15)
                      </span>
                    }
                    @case ('IN_REVIEW') {
                      <span class="badge badge-warning gap-1 font-semibold text-xs animate-pulse">
                        <span class="w-1.5 h-1.5 rounded-full bg-warning-content"></span>
                        Em Conferência Manual
                      </span>
                    }
                    @case ('DOCUMENTS_RECEIVED') {
                      <span class="badge badge-info gap-1 font-semibold text-xs">
                        <span class="w-1.5 h-1.5 rounded-full bg-info-content"></span>
                        Documentos Recebidos
                      </span>
                    }
                    @default {
                      <span class="badge badge-ghost gap-1 font-semibold text-xs">
                        <span class="w-1.5 h-1.5 rounded-full bg-base-content/40"></span>
                        Pendente
                      </span>
                    }
                  }
                </div>
                <p class="text-xs text-base-content/50 font-mono mt-0.5">ID: {{ persona()?.id }}</p>
              </div>

              <!-- Quick Action Buttons -->
              <div class="flex flex-wrap gap-2">
                <button (click)="openUploadModal()" class="btn btn-outline btn-sm gap-1.5">
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                  </svg>
                  Upload Interno
                </button>
                <button (click)="generateLink()" class="btn btn-primary btn-sm gap-1.5 shadow-xs">
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                  </svg>
                  Gerar Link de Coleta (48h)
                </button>
              </div>
            </div>

            <!-- Details metadata grid -->
            <div class="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-6 pt-6 border-t border-base-200 text-xs">
              <div>
                <span class="text-base-content/50 block">CPF do Titular</span>
                <span class="font-mono font-semibold text-base-content mt-0.5 block">
                  {{ persona()?.cpf || 'Não cadastrado' }}
                </span>
              </div>
              <div>
                <span class="text-base-content/50 block">E-mail</span>
                <span class="font-medium text-base-content mt-0.5 block truncate">
                  {{ persona()?.email || '—' }}
                </span>
              </div>
              <div>
                <span class="text-base-content/50 block">Telefone</span>
                <span class="font-medium text-base-content mt-0.5 block">
                  {{ persona()?.phone || '—' }}
                </span>
              </div>
              <div>
                <span class="text-base-content/50 block">Documentos Exigidos</span>
                <div class="flex flex-wrap gap-1 mt-0.5">
                  @for (req of persona()?.required_document_types; track req) {
                    <span class="badge badge-neutral badge-xs">{{ req }}</span>
                  }
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Documents Section Header -->
        <div class="flex justify-between items-center">
          <div class="flex items-center space-x-2">
            <h2 class="text-lg font-bold text-base-content">Documentos Anexados</h2>
            <span class="badge badge-neutral badge-sm">{{ documents().length }}</span>
          </div>
          <button (click)="loadDocuments()" class="btn btn-ghost btn-xs gap-1 text-base-content/70">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Atualizar
          </button>
        </div>

        <!-- Documents Table -->
        <div class="card bg-base-100 border border-base-200 shadow-xs overflow-hidden">
          <div class="overflow-x-auto">
            <table class="table table-zebra w-full text-sm">
              <thead>
                <tr class="bg-base-200/50 text-base-content/70 text-xs">
                  <th>Documento / Arquivo</th>
                  <th>Origem</th>
                  <th>Status de Validação</th>
                  <th>Confiança OCR</th>
                  <th>Data de Envio</th>
                  <th class="text-right">Ação</th>
                </tr>
              </thead>
              <tbody>
                @if (loadingDocs()) {
                  <tr>
                    <td colspan="6" class="text-center py-8">
                      <span class="loading loading-spinner loading-md text-primary"></span>
                    </td>
                  </tr>
                } @else if (documents().length === 0) {
                  <tr>
                    <td colspan="6" class="text-center py-10 text-base-content/60">
                      Nenhum documento enviado ainda. Utilize o botão "Upload Interno" ou gere um Link de Coleta.
                    </td>
                  </tr>
                } @else {
                  @for (doc of documents(); track doc.id) {
                    <tr class="hover:bg-base-200/40">
                      <td>
                        <div class="flex items-center space-x-3">
                          <div class="p-2 bg-base-200 rounded-lg text-primary">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                            </svg>
                          </div>
                          <div>
                            <div class="font-bold text-xs">{{ doc.sanitized_file_name || doc.raw_file_name }}</div>
                            <div class="text-[11px] text-base-content/50 font-mono">{{ (doc.file_size_bytes / 1024).toFixed(1) }} KB • {{ doc.mime_type }}</div>
                          </div>
                        </div>
                      </td>
                      <td>
                        <span class="badge badge-ghost badge-xs">{{ doc.upload_origin }}</span>
                      </td>
                      <td>
                        @switch (doc.status) {
                          @case ('READY') {
                            <span class="badge badge-success badge-sm font-semibold">Aprovado (READY)</span>
                          }
                          @case ('NEEDS_REVIEW') {
                            <span class="badge badge-warning badge-sm font-semibold animate-pulse">
                              Revisão Humana (RN-01)
                            </span>
                          }
                          @case ('PROCESSING') {
                            <span class="badge badge-info badge-sm font-semibold gap-1">
                              <span class="loading loading-spinner loading-xs"></span>
                              Processando OCR
                            </span>
                          }
                          @case ('REJECTED') {
                            <span class="badge badge-error badge-sm font-semibold">Rejeitado (RN-09)</span>
                          }
                          @default {
                            <span class="badge badge-ghost badge-sm">{{ doc.status }}</span>
                          }
                        }
                      </td>
                      <td>
                        @if (doc.confidence_score !== null && doc.confidence_score !== undefined) {
                          <div class="flex items-center space-x-2">
                            <progress
                              class="progress w-16 h-2"
                              [ngClass]="doc.confidence_score >= 0.85 ? 'progress-success' : 'progress-warning'"
                              [value]="doc.confidence_score * 100"
                              max="100"
                            ></progress>
                            <span class="text-xs font-mono font-semibold">
                              {{ (doc.confidence_score * 100).toFixed(0) }}%
                            </span>
                          </div>
                        } @else {
                          <span class="text-xs text-base-content/40">—</span>
                        }
                      </td>
                      <td class="text-xs text-base-content/60">
                        {{ doc.created_at | date: 'dd/MM/yyyy HH:mm' }}
                      </td>
                      <td class="text-right">
                        <div class="flex justify-end gap-2">
                          @if (doc.preview_url) {
                            <a
                              [href]="doc.preview_url"
                              target="_blank"
                              class="btn btn-ghost btn-xs tooltip"
                              data-tip="Abrir Imagem Original"
                            >
                              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                              </svg>
                            </a>
                          }
                          @if (doc.status === 'NEEDS_REVIEW' || doc.status === 'READY') {
                            <a
                              [routerLink]="['/documents', doc.id, 'review']"
                              class="btn btn-sm btn-xs"
                              [ngClass]="doc.status === 'NEEDS_REVIEW' ? 'btn-warning text-warning-content' : 'btn-outline'"
                            >
                              {{ doc.status === 'NEEDS_REVIEW' ? 'Conferir Lado a Lado' : 'Visualizar Dados' }}
                            </a>
                          }
                        </div>
                      </td>
                    </tr>
                  }
                }
              </tbody>
            </table>
          </div>
        </div>
      }
    </div>

    <!-- Modal Upload Interno de Documento -->
    @if (isUploadModalOpen()) {
      <div class="modal modal-open">
        <div class="modal-box max-w-md">
          <h3 class="font-bold text-lg text-base-content mb-3">Upload de Documento (Operador)</h3>
          <p class="text-xs text-base-content/60 mb-4">
            Envie uma imagem de documento (CIN ou RG) para extração e validação assíncrona via OCR.
          </p>

          <div class="space-y-4">
            <div class="form-control">
              <label class="label py-1"><span class="label-text text-xs font-semibold">Tipo do Documento</span></label>
              <select [(ngModel)]="uploadDocType" class="select select-bordered select-sm w-full text-xs">
                <option value="CIN">CIN - Carteira de Identidade Nacional</option>
                <option value="RG_ANTIGO">RG - Registro Geral Tradicional</option>
              </select>
            </div>

            <div class="form-control">
              <label class="label py-1"><span class="label-text text-xs font-semibold">Arquivo (PNG, JPEG, PDF)</span></label>
              <input
                type="file"
                (change)="onFileSelected($event)"
                accept="image/png,image/jpeg,image/jpg,application/pdf"
                class="file-input file-input-bordered file-input-sm w-full"
              />
            </div>
          </div>

          <div class="modal-action mt-6">
            <button (click)="closeUploadModal()" class="btn btn-ghost btn-sm" [disabled]="uploading()">
              Cancelar
            </button>
            <button
              (click)="submitUpload()"
              class="btn btn-primary btn-sm"
              [disabled]="uploading() || !selectedFile"
            >
              @if (uploading()) {
                <span class="loading loading-spinner loading-xs"></span>
              }
              Iniciar Processamento OCR
            </button>
          </div>
        </div>
      </div>
    }

    <!-- Modal Link de Coleta -->
    @if (generatedLink()) {
      <div class="modal modal-open">
        <div class="modal-box max-w-lg">
          <h3 class="font-bold text-lg text-base-content mb-2">Link de Coleta Criado!</h3>
          <p class="text-xs text-base-content/70 mb-4 leading-relaxed">
            Envie este link para o titular. Ele poderá fotografar seus documentos pelo celular com a câmera inteligente.
          </p>

          <div class="bg-base-200 p-3 rounded-lg flex items-center justify-between gap-2 mb-4">
            <input
              type="text"
              readonly
              [value]="clientUploadUrl"
              class="input input-sm input-ghost w-full font-mono text-xs focus:outline-hidden"
            />
            <button (click)="copyLinkToClipboard()" class="btn btn-sm btn-primary shrink-0">
              Copiar
            </button>
          </div>

          <div class="modal-action">
            <button (click)="generatedLink.set(null)" class="btn btn-sm btn-neutral w-full">
              Fechar
            </button>
          </div>
        </div>
      </div>
    }
  `,
})
export class PersonaDetailComponent implements OnInit {
  private route = inject(ActivatedRoute);
  private personaService = inject(PersonaService);
  private documentService = inject(DocumentService);
  private notificationService = inject(NotificationService);
  private toastService = inject(ToastService);

  public persona = signal<Persona | null>(null);
  public documents = signal<DocumentRead[]>([]);
  public loadingPersona = signal<boolean>(false);
  public loadingDocs = signal<boolean>(false);
  public isUploadModalOpen = signal<boolean>(false);
  public uploading = signal<boolean>(false);
  public generatedLink = signal<CollectionLinkResponse | null>(null);

  public uploadDocType = 'CIN';
  public selectedFile: File | null = null;
  private personaId = '';

  constructor() {
    effect(() => {
      const event = this.notificationService.latestEvent();
      if (event && (event.event.startsWith('document.') || event.event.startsWith('persona.'))) {
        this.loadDocuments();
        this.loadPersona();
      }
    });
  }

  public ngOnInit(): void {
    this.personaId = this.route.snapshot.paramMap.get('id') || '';
    if (this.personaId) {
      this.loadPersona();
      this.loadDocuments();
    }
  }

  public get clientUploadUrl(): string {
    const link = this.generatedLink();
    if (!link) return '';
    const token = link.token || link.public_token || '';
    const origin = window.location.origin;
    return `${origin}/public/upload?token=${encodeURIComponent(token)}`;
  }

  public loadPersona(): void {
    this.loadingPersona.set(true);
    this.personaService.get(this.personaId).subscribe({
      next: (p) => {
        this.persona.set(p);
        this.loadingPersona.set(false);
      },
      error: () => this.loadingPersona.set(false),
    });
  }

  public loadDocuments(): void {
    this.loadingDocs.set(true);
    this.documentService.list({ personaId: this.personaId }).subscribe({
      next: (docs) => {
        this.documents.set(docs);
        this.loadingDocs.set(false);
      },
      error: () => this.loadingDocs.set(false),
    });
  }

  public openUploadModal(): void {
    this.selectedFile = null;
    this.isUploadModalOpen.set(true);
  }

  public closeUploadModal(): void {
    this.isUploadModalOpen.set(false);
  }

  public onFileSelected(event: any): void {
    const file = event.target?.files?.[0];
    if (file) {
      this.selectedFile = file;
    }
  }

  public submitUpload(): void {
    if (!this.selectedFile) return;
    this.uploading.set(true);

    this.documentService.uploadInternal(this.personaId, this.selectedFile, this.uploadDocType).subscribe({
      next: () => {
        this.uploading.set(false);
        this.toastService.success('Documento enviado para processamento assíncrono!');
        this.closeUploadModal();
        this.loadDocuments();
      },
      error: () => this.uploading.set(false),
    });
  }

  public generateLink(): void {
    this.personaService.createCollectionLink(this.personaId).subscribe({
      next: (resp) => this.generatedLink.set(resp),
      error: () => this.toastService.error('Erro ao gerar link de coleta.'),
    });
  }

  public copyLinkToClipboard(): void {
    if (!this.clientUploadUrl) return;
    navigator.clipboard.writeText(this.clientUploadUrl).then(() => {
      this.toastService.info('Link copiado!');
    });
  }
}
