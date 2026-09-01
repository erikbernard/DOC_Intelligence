import { Component, OnDestroy, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { DocumentService } from '../../core/services/document.service';
import { AuthService } from '../../core/services/auth.service';
import { ToastService } from '../../core/services/toast.service';
import { DocumentDetailRead, DocumentReviewUpdate } from '../../core/models/document.model';

export interface ReviewFormData {
  cpf: string;
  nome_completo: string;
  data_nascimento: string;
  data_validade: string;
  naturalidade: string;
  nacionalidade: string;
  rg_numero: string;
}

@Component({
  selector: 'app-document-review',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  template: `
    <div class="h-[calc(100vh-6.5rem)] flex flex-col space-y-3">
      <!-- Top Action Bar & Lock Banner -->
      <div class="flex flex-wrap items-center justify-between gap-3 bg-base-100 px-4 py-2.5 rounded-xl border border-base-200 shadow-xs">
        <div class="flex items-center space-x-3">
          <button (click)="cancelAndUnlock()" class="btn btn-ghost btn-sm gap-1">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            Voltar
          </button>
          <div class="divider divider-horizontal my-0"></div>
          <div>
            <h1 class="font-bold text-sm text-base-content flex items-center gap-2">
              Conferência Humana Lado a Lado (RN-10)
              <span class="badge badge-warning badge-sm font-semibold">Pessimistic Lock Ativo</span>
            </h1>
            <span class="text-[11px] text-base-content/50 font-mono">
              Documento: {{ document()?.id }}
            </span>
          </div>
        </div>

        <!-- Lock info and Actions -->
        <div class="flex items-center space-x-2">
          <button
            (click)="openRejectModal()"
            class="btn btn-outline btn-error btn-sm"
            [disabled]="processing()"
          >
            Rejeitar por Ilegibilidade (RN-09)
          </button>
          <button
            (click)="submitReview()"
            class="btn btn-success btn-sm text-success-content font-bold shadow-sm"
            [disabled]="processing()"
          >
            @if (processing()) {
              <span class="loading loading-spinner loading-xs"></span>
            }
            Aprovar Conferência (RN-10)
          </button>
        </div>
      </div>

      <!-- Main Split View Container -->
      <div class="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-3 min-h-0">
        <!-- LEFT: Interactive Image/PDF Viewer (Col 7) -->
        <div class="lg:col-span-7 bg-neutral-900 rounded-xl overflow-hidden flex flex-col relative border border-neutral-700 shadow-inner">
          <!-- Viewer Toolbar -->
          <div class="bg-neutral-800/90 text-neutral-content px-3 py-1.5 flex items-center justify-between text-xs z-10">
            <span class="font-mono text-[11px] truncate max-w-xs">
              {{ document()?.sanitized_file_name || 'Documento Original' }}
            </span>

            <div class="flex items-center space-x-1.5">
              <button (click)="zoomOut()" class="btn btn-ghost btn-xs text-white" title="Reduzir Zoom (-)">
                🔍-
              </button>
              <span class="font-mono text-[11px] px-1">{{ (zoomLevel * 100).toFixed(0) }}%</span>
              <button (click)="zoomIn()" class="btn btn-ghost btn-xs text-white" title="Aumentar Zoom (+)">
                🔍+
              </button>
              <button (click)="resetZoom()" class="btn btn-ghost btn-xs text-white" title="Redefinir">
                100%
              </button>
              <button (click)="rotate()" class="btn btn-ghost btn-xs text-white" title="Girar 90°">
                ↻ Girar
              </button>
              @if (imageUrl) {
                <a [href]="imageUrl" target="_blank" class="btn btn-ghost btn-xs text-primary" title="Abrir em nova aba">
                  ↗
                </a>
              }
            </div>
          </div>

          <!-- Image Canvas Area -->
          <div class="flex-1 overflow-auto flex items-center justify-center p-4 select-none cursor-grab active:cursor-grabbing">
            @if (loadingDoc()) {
              <span class="loading loading-spinner loading-lg text-primary"></span>
            } @else if (imageUrl) {
              <img
                [src]="imageUrl"
                alt="Documento para conferência"
                [style.transform]="'scale(' + zoomLevel + ') rotate(' + rotationDeg + 'deg)'"
                class="max-h-full max-w-full object-contain rounded-sm shadow-2xl transition-transform duration-150"
              />
            } @else {
              <div class="text-neutral-400 text-xs">Imagem não disponível para pré-visualização.</div>
            }
          </div>
        </div>

        <!-- RIGHT: Form & Audit Panel (Col 5) -->
        <div class="lg:col-span-5 bg-base-100 rounded-xl border border-base-200 shadow-xs flex flex-col overflow-hidden">
          <div class="p-3 bg-base-200/50 border-b border-base-200 flex justify-between items-center">
            <span class="font-bold text-xs uppercase tracking-wider text-base-content/70">
              Dados Extraídos & Correção
            </span>
            <div class="flex items-center space-x-1.5">
              <span class="text-[11px] text-base-content/60">Template:</span>
              <select
                [(ngModel)]="selectedTemplateCode"
                class="select select-bordered select-xs text-xs font-bold"
              >
                <option value="CIN">CIN (Nova Identidade)</option>
                <option value="RG_ANTIGO">RG Clássico</option>
                <option value="CNH">CNH</option>
              </select>
            </div>
          </div>

          <!-- Validation Warnings Alert if any -->
          @if (validationErrors.length > 0) {
            <div class="p-3 bg-warning/10 border-b border-warning/20">
              <div class="flex items-start space-x-2 text-warning text-xs">
                <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-4 w-4 mt-0.5" fill="none" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
                <div>
                  <strong class="font-bold">Avisos da Extração OCR:</strong>
                  <ul class="list-disc list-inside mt-1 space-y-0.5 text-[11px]">
                    @for (err of validationErrors; track err) {
                      <li>{{ err }}</li>
                    }
                  </ul>
                </div>
              </div>
            </div>
          }

          <!-- Editable Fields Form Scrollable -->
          <div class="flex-1 overflow-y-auto p-4 space-y-3">
            <!-- CPF Field -->
            <div class="form-control">
              <div class="flex justify-between items-center mb-1">
                <label class="label-text text-xs font-semibold text-base-content">CPF do Titular *</label>
                <span class="badge badge-xs" [ngClass]="isFieldValid('cpf') ? 'badge-success' : 'badge-warning'">
                  Confiança: {{ getFieldConfidence('cpf') }}%
                </span>
              </div>
              <input
                type="text"
                [(ngModel)]="formData.cpf"
                name="cpf"
                placeholder="000.000.000-00"
                class="input input-bordered input-sm w-full font-mono text-xs focus:input-primary"
              />
              <span class="text-[10px] text-base-content/50 mt-0.5">
                Validação criptográfica Módulo 11 (RN-04)
              </span>
            </div>

            <!-- Nome Completo Field -->
            <div class="form-control">
              <div class="flex justify-between items-center mb-1">
                <label class="label-text text-xs font-semibold text-base-content">Nome Completo *</label>
                <span class="badge badge-xs" [ngClass]="isFieldValid('nome_completo') ? 'badge-success' : 'badge-warning'">
                  Confiança: {{ getFieldConfidence('nome_completo') }}%
                </span>
              </div>
              <input
                type="text"
                [(ngModel)]="formData.nome_completo"
                name="nome_completo"
                placeholder="NOME COMPLETO"
                class="input input-bordered input-sm w-full uppercase text-xs focus:input-primary"
              />
            </div>

            <!-- Data de Nascimento & Data de Validade -->
            <div class="grid grid-cols-2 gap-2">
              <div class="form-control">
                <label class="label-text text-xs font-semibold text-base-content mb-1">Nascimento *</label>
                <input
                  type="text"
                  [(ngModel)]="formData.data_nascimento"
                  name="data_nascimento"
                  placeholder="DD/MM/AAAA"
                  class="input input-bordered input-sm w-full font-mono text-xs focus:input-primary"
                />
              </div>

              <div class="form-control">
                <label class="label-text text-xs font-semibold text-base-content mb-1">Validade</label>
                <input
                  type="text"
                  [(ngModel)]="formData.data_validade"
                  name="data_validade"
                  placeholder="DD/MM/AAAA"
                  class="input input-bordered input-sm w-full font-mono text-xs focus:input-primary"
                />
              </div>
            </div>

            <!-- Naturalidade & Nacionalidade -->
            <div class="grid grid-cols-2 gap-2">
              <div class="form-control">
                <div class="flex justify-between items-center mb-1">
                  <label class="label-text text-xs font-semibold text-base-content">Naturalidade</label>
                  @if (isFuzzyCorrected('naturalidade')) {
                    <span class="badge badge-info badge-xs text-[9px]">Fuzzy (RN-03)</span>
                  }
                </div>
                <input
                  type="text"
                  [(ngModel)]="formData.naturalidade"
                  name="naturalidade"
                  placeholder="CIDADE - UF"
                  class="input input-bordered input-sm w-full uppercase text-xs focus:input-primary"
                />
              </div>

              <div class="form-control">
                <label class="label-text text-xs font-semibold text-base-content mb-1">Nacionalidade</label>
                <input
                  type="text"
                  [(ngModel)]="formData.nacionalidade"
                  name="nacionalidade"
                  placeholder="BRASILEIRA"
                  class="input input-bordered input-sm w-full uppercase text-xs focus:input-primary"
                />
              </div>
            </div>

            <!-- Número RG (se RG Antigo) -->
            @if (selectedTemplateCode === 'RG_ANTIGO') {
              <div class="form-control">
                <label class="label-text text-xs font-semibold text-base-content mb-1">Número do RG</label>
                <input
                  type="text"
                  [(ngModel)]="formData.rg_numero"
                  name="rg_numero"
                  placeholder="Número do RG"
                  class="input input-bordered input-sm w-full font-mono text-xs focus:input-primary"
                />
              </div>
            }

            <!-- Observações da Revisão Manual -->
            <div class="form-control pt-2 border-t border-base-200">
              <label class="label-text text-xs font-semibold text-base-content mb-1">
                Parecer do Operador (Auditoria)
              </label>
              <textarea
                [(ngModel)]="operatorNotes"
                name="operatorNotes"
                rows="2"
                placeholder="Observações ou justificativa de correção manual..."
                class="textarea textarea-bordered text-xs focus:textarea-primary"
              ></textarea>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Modal Rejeição -->
    @if (isRejectModalOpen()) {
      <div class="modal modal-open">
        <div class="modal-box max-w-sm">
          <h3 class="font-bold text-base text-error mb-2">Rejeitar Documento (RN-09)</h3>
          <p class="text-xs text-base-content/70 mb-4">
            Informe o motivo da rejeição. O titular será notificado para enviar uma nova foto mais nítida.
          </p>

          <textarea
            [(ngModel)]="rejectionReason"
            rows="3"
            placeholder="Ex: Imagem muito borrada, reflexo sobre o número do CPF..."
            class="textarea textarea-bordered w-full text-xs"
          ></textarea>

          <div class="modal-action">
            <button (click)="isRejectModalOpen.set(false)" class="btn btn-ghost btn-sm" [disabled]="processing()">
              Cancelar
            </button>
            <button
              (click)="confirmReject()"
              class="btn btn-error btn-sm text-white"
              [disabled]="processing() || !rejectionReason.trim()"
            >
              Confirmar Rejeição
            </button>
          </div>
        </div>
      </div>
    }
  `,
})
export class DocumentReviewComponent implements OnInit, OnDestroy {
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private documentService = inject(DocumentService);
  private authService = inject(AuthService);
  private toastService = inject(ToastService);

  public documentId = '';
  public document = signal<DocumentDetailRead | null>(null);
  public loadingDoc = signal<boolean>(false);
  public processing = signal<boolean>(false);
  public isRejectModalOpen = signal<boolean>(false);

  public selectedTemplateCode = 'CIN';
  public operatorNotes = 'Campos conferidos e aprovados manualmente pelo operador.';
  public rejectionReason = '';
  public validationErrors: string[] = [];

  public formData: ReviewFormData = {
    cpf: '',
    nome_completo: '',
    data_nascimento: '',
    data_validade: '',
    naturalidade: '',
    nacionalidade: '',
    rg_numero: '',
  };

  // Viewer state
  public zoomLevel = 1.0;
  public rotationDeg = 0;

  public ngOnInit(): void {
    this.documentId = this.route.snapshot.paramMap.get('id') || '';
    if (this.documentId) {
      this.acquireLockAndLoad();
    }
  }

  public ngOnDestroy(): void {
    // Unlock document when leaving screen
    if (this.documentId) {
      this.documentService.unlock(this.documentId).subscribe();
    }
  }

  public get imageUrl(): string {
    const doc = this.document();
    if (!doc) return '';
    if (doc.preview_url) return doc.preview_url;
    // Fallback using direct stream with token
    const token = this.authService.token();
    return `http://localhost:8000/api/v1/documents/${this.documentId}/file?token=${token}`;
  }

  private acquireLockAndLoad(): void {
    this.loadingDoc.set(true);

    // Acquire lock (RN-07 / RN-08)
    this.documentService.lock(this.documentId).subscribe({
      next: () => {
        this.fetchDocument();
      },
      error: () => {
        // If lock failed due to 409 conflict, still fetch to allow read-only view
        this.fetchDocument();
      },
    });
  }

  private fetchDocument(): void {
    this.documentService.get(this.documentId).subscribe({
      next: (doc) => {
        this.document.set(doc);
        this.loadingDoc.set(false);
        this.populateForm(doc);
      },
      error: () => this.loadingDoc.set(false),
    });
  }

  private populateForm(doc: DocumentDetailRead): void {
    const extracted = doc.extracted_data || {};
    this.selectedTemplateCode = extracted.template_code || 'CIN';
    this.validationErrors = extracted.validation_errors || [];

    const fields = extracted.fields || {};
    const keys: (keyof ReviewFormData)[] = [
      'cpf',
      'nome_completo',
      'data_nascimento',
      'data_validade',
      'naturalidade',
      'nacionalidade',
      'rg_numero',
    ];
    for (const key of keys) {
      if (fields[key] && fields[key].value !== undefined) {
        this.formData[key] = fields[key].value || '';
      }
    }
  }

  public isFieldValid(fieldName: string): boolean {
    const fields = this.document()?.extracted_data?.fields || {};
    return fields[fieldName]?.is_valid ?? true;
  }

  public getFieldConfidence(fieldName: string): string {
    const fields = this.document()?.extracted_data?.fields || {};
    const conf = fields[fieldName]?.confidence;
    if (conf !== undefined && conf !== null) {
      return (conf * 100).toFixed(0);
    }
    return '100';
  }

  public isFuzzyCorrected(fieldName: string): boolean {
    const fields = this.document()?.extracted_data?.fields || {};
    return fields[fieldName]?.is_fuzzy_corrected ?? false;
  }

  public zoomIn(): void {
    this.zoomLevel = Math.min(3.0, this.zoomLevel + 0.25);
  }

  public zoomOut(): void {
    this.zoomLevel = Math.max(0.5, this.zoomLevel - 0.25);
  }

  public resetZoom(): void {
    this.zoomLevel = 1.0;
    this.rotationDeg = 0;
  }

  public rotate(): void {
    this.rotationDeg = (this.rotationDeg + 90) % 360;
  }

  public submitReview(): void {
    this.processing.set(true);

    const payload: DocumentReviewUpdate = {
      template_code: this.selectedTemplateCode,
      document_type: this.selectedTemplateCode,
      corrected_data: this.formData,
      notes: this.operatorNotes,
    };

    this.documentService.review(this.documentId, payload).subscribe({
      next: (updated) => {
        this.processing.set(false);
        this.toastService.success('Conferência aprovada com sucesso! Documento agora é READY.');
        const personaId = updated.persona_id;
        this.router.navigate(['/personas', personaId]);
      },
      error: () => this.processing.set(false),
    });
  }

  public openRejectModal(): void {
    this.rejectionReason = '';
    this.isRejectModalOpen.set(true);
  }

  public confirmReject(): void {
    if (!this.rejectionReason.trim()) return;
    this.processing.set(true);

    this.documentService.reject(this.documentId, { rejection_reason: this.rejectionReason }).subscribe({
      next: (updated) => {
        this.processing.set(false);
        this.isRejectModalOpen.set(false);
        this.toastService.warning('Documento rejeitado por baixa qualidade.');
        this.router.navigate(['/personas', updated.persona_id]);
      },
      error: () => this.processing.set(false),
    });
  }

  public cancelAndUnlock(): void {
    const personaId = this.document()?.persona_id;
    if (personaId) {
      this.router.navigate(['/personas', personaId]);
    } else {
      this.router.navigate(['/personas']);
    }
  }
}
