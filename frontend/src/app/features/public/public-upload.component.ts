import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute } from '@angular/router';
import { DocumentService } from '../../core/services/document.service';
import { ToastService } from '../../core/services/toast.service';
import { ToastContainerComponent } from '../../layout/toast-container/toast-container.component';
import { CameraModalComponent } from './camera-modal.component';
import { TemplateCardComponent } from './template-card.component';
import { StagedDocsComponent, StagedDocument } from './staged-docs.component';

@Component({
  selector: 'app-public-upload',
  standalone: true,
  imports: [
    CommonModule,
    ToastContainerComponent,
    CameraModalComponent,
    TemplateCardComponent,
    StagedDocsComponent,
  ],
  template: `
    <div class="min-h-screen bg-base-200 flex flex-col justify-between py-6 px-4 sm:px-6">
      <div class="max-w-md w-full mx-auto space-y-5">
        <!-- Brand / Header -->
        <div class="text-center space-y-1">
          <div class="inline-flex items-center space-x-1.5 px-3 py-1 bg-primary/10 text-primary rounded-full text-xs font-semibold">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
            <span>Ambiente Seguro Criptografado</span>
          </div>
          <h1 class="text-xl font-bold text-base-content mt-2">Envio de Documento de Identidade</h1>
          <p class="text-xs text-base-content/60">
            Fotografe ou anexe seu documento oficial para validação do cadastro.
          </p>
        </div>

        @if (!token) {
          <!-- Invalid or missing token warning -->
          <div class="alert alert-error text-xs p-4 rounded-xl shadow-xs">
            <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-5 w-5" fill="none" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
            <div>
              <h3 class="font-bold">Link de Envio Inválido</h3>
              <div class="text-xs mt-0.5">O token de segurança não foi informado ou o link expirou (limite de 48h).</div>
            </div>
          </div>
        } @else if (submittedSuccess()) {
          <!-- Success Screen -->
          <div class="card bg-base-100 border border-success/30 shadow-xl p-6 text-center space-y-4">
            <div class="w-16 h-16 rounded-full bg-success/10 text-success flex items-center justify-center mx-auto">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-10 w-10" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h2 class="text-lg font-bold text-base-content">Documentos Enviados com Sucesso!</h2>
            <p class="text-xs text-base-content/70 leading-relaxed">
              Recebemos seus arquivos com sucesso. Nosso sistema de inteligência artificial e conferência documental já está analisando as informações com conformidade e segurança.
            </p>
            <div class="p-3 bg-base-200/60 rounded-lg text-[11px] text-base-content/60 font-mono">
              Você já pode fechar esta página com segurança.
            </div>
          </div>
        } @else {
          <!-- Interactive Upload Workflow Form -->
          <div class="card bg-base-100 border border-base-200 shadow-md p-5 space-y-5">
            <!-- Step 1: Select Document Type via Visual Cards -->
            <div class="space-y-2">
              <label class="text-xs font-bold text-base-content/70 uppercase tracking-wider block">
                1. Selecione o Tipo de Documento
              </label>
              <app-template-card
                [selectedCode]="selectedTemplateCode()"
                (selected)="selectedTemplateCode.set($event)"
              />
            </div>

            <!-- Step 2: Capture Options Buttons -->
            <div class="space-y-2">
              <label class="text-xs font-bold text-base-content/70 uppercase tracking-wider block">
                2. Escolha como Enviar
              </label>
              <div class="grid grid-cols-2 gap-3">
                <!-- Camera Button -->
                <button
                  type="button"
                  (click)="openCamera()"
                  class="btn btn-outline btn-primary flex flex-col h-auto py-3 gap-1 rounded-xl"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                  <span class="text-xs font-bold">Tirar Foto</span>
                  <span class="text-[10px] opacity-70">Câmera com guia</span>
                </button>

                <!-- Attach File Button -->
                <label
                  class="btn btn-outline flex flex-col h-auto py-3 gap-1 rounded-xl cursor-pointer"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                  </svg>
                  <span class="text-xs font-bold">Anexar Arquivo</span>
                  <span class="text-[10px] opacity-70">PDF, PNG ou JPG</span>
                  <input
                    type="file"
                    (change)="onFileAttached($event)"
                    accept="image/png,image/jpeg,image/jpg,application/pdf"
                    class="hidden"
                  />
                </label>
              </div>
            </div>

            <!-- Step 3: Staged items gallery -->
            @if (stagedDocs().length > 0) {
              <div class="pt-2 border-t border-base-200">
                <app-staged-docs
                  [items]="stagedDocs()"
                  (remove)="removeStagedDoc($event)"
                />
              </div>
            }

            <!-- Step 4: Submit button -->
            <div class="pt-2">
              <button
                type="button"
                (click)="submitAllDocuments()"
                class="btn btn-primary w-full shadow-md"
                [disabled]="stagedDocs().length === 0 || uploading()"
              >
                @if (uploading()) {
                  <span class="loading loading-spinner loading-sm"></span>
                  Enviando Documentos...
                } @else {
                  Enviar Documentos ({{ stagedDocs().length }})
                }
              </button>
              <p class="text-[10px] text-base-content/50 text-center mt-2">
                Conformidade com a LGPD e exclusão garantida pelo titular (RN-13).
              </p>
            </div>
          </div>
        }
      </div>

      <!-- Footer Branding -->
      <footer class="text-center text-xs text-base-content/40 mt-6">
        DOC_Intelligence • Onboarding Digital Seguro
      </footer>
    </div>

    <!-- Live Camera Modal with Reticle/Viewfinder -->
    @if (isCameraOpen()) {
      <app-camera-modal
        (captured)="onPhotoCaptured($event)"
        (closed)="isCameraOpen.set(false)"
      />
    }

    <!-- Floating Toasts -->
    <app-toast-container />
  `,
})
export class PublicUploadComponent implements OnInit {
  private route = inject(ActivatedRoute);
  private documentService = inject(DocumentService);
  private toastService = inject(ToastService);

  public token: string | null = null;
  public selectedTemplateCode = signal<string>('CIN');
  public stagedDocs = signal<StagedDocument[]>([]);
  public isCameraOpen = signal<boolean>(false);
  public uploading = signal<boolean>(false);
  public submittedSuccess = signal<boolean>(false);

  public ngOnInit(): void {
    this.token = this.route.snapshot.queryParamMap.get('token');
  }

  public openCamera(): void {
    this.isCameraOpen.set(true);
  }

  public onPhotoCaptured(file: File): void {
    this.isCameraOpen.set(false);
    this.addStagedFile(file);
    this.toastService.success('Foto capturada com enquadramento!');
  }

  public onFileAttached(event: any): void {
    const file = event.target?.files?.[0];
    if (file) {
      this.addStagedFile(file);
      this.toastService.info('Arquivo anexado com sucesso!');
      event.target.value = '';
    }
  }

  private addStagedFile(file: File): void {
    const id = Math.random().toString(36).substring(2, 9);
    const previewUrl = URL.createObjectURL(file);
    const item: StagedDocument = {
      id,
      file,
      previewUrl,
      documentType: this.selectedTemplateCode(),
    };

    this.stagedDocs.update((current) => [...current, item]);
  }

  public removeStagedDoc(id: string): void {
    this.stagedDocs.update((current) => {
      const target = current.find((d) => d.id === id);
      if (target?.previewUrl) {
        URL.revokeObjectURL(target.previewUrl);
      }
      return current.filter((d) => d.id !== id);
    });
  }

  public async submitAllDocuments(): Promise<void> {
    if (!this.token || this.stagedDocs().length === 0) return;
    this.uploading.set(true);

    try {
      for (const item of this.stagedDocs()) {
        await new Promise((resolve, reject) => {
          this.documentService
            .uploadPublic(this.token!, item.file, item.documentType)
            .subscribe({
              next: () => resolve(true),
              error: (err: any) => reject(err),
            });
        });
      }

      this.uploading.set(false);
      this.submittedSuccess.set(true);
      this.toastService.success('Todos os documentos foram enviados com sucesso!');
    } catch (err) {
      this.uploading.set(false);
      this.toastService.error('Erro ao enviar um ou mais documentos. Tente novamente.');
    }
  }
}
