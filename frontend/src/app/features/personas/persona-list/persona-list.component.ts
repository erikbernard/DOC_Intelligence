import { Component, OnInit, computed, effect, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { PersonaService } from '../../../core/services/persona.service';
import { NotificationService } from '../../../core/services/notification.service';
import { ToastService } from '../../../core/services/toast.service';
import { Persona, PersonaCreate, PersonaStatus } from '../../../core/models/persona.model';
import { CollectionLinkResponse } from '../../../core/models/collection-link.model';
import {
  formatCpf,
  formatPhone,
  validateCpf,
  validateEmail,
  validatePhone,
} from '../../../core/utils/validators';

@Component({
  selector: 'app-persona-list',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  template: `
    <div class="space-y-6">
      <!-- Top Title & Action Bar -->
      <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-base-100 p-5 rounded-2xl border border-base-200 shadow-xs">
        <div>
          <h1 class="text-2xl font-bold text-base-content">Personas & Onboarding</h1>
          <p class="text-sm text-base-content/60 mt-0.5">
            Gerenciamento de titulares, validação de identidades e links de coleta.
          </p>
        </div>
        <button (click)="openCreateModal()" class="btn btn-primary btn-sm sm:btn-md gap-2 shadow-sm">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
          </svg>
          Nova Persona
        </button>
      </div>

      <!-- Filters & Search Bar -->
      <div class="card bg-base-100 border border-base-200 shadow-xs">
        <div class="card-body p-4 flex flex-col md:flex-row gap-3 items-center justify-between">
          <!-- Search input with real-time reactive filtering -->
          <div class="relative w-full md:w-80">
            <input
              type="text"
              [ngModel]="searchQuery()"
              (ngModelChange)="onSearchChange($event)"
              placeholder="Buscar por nome, CPF ou e-mail..."
              class="input input-bordered input-sm w-full pl-9"
            />
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 absolute left-3 top-2.5 text-base-content/40" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            @if (searchQuery()) {
              <button
                (click)="clearSearch()"
                class="btn btn-ghost btn-xs btn-circle absolute right-2 top-1.5 text-base-content/50"
                title="Limpar busca"
              >
                ✕
              </button>
            }
          </div>

          <!-- Status Filter Tabs -->
          <div class="flex flex-wrap gap-1.5 items-center w-full md:w-auto">
            <button
              (click)="setStatusFilter(undefined)"
              class="btn btn-xs"
              [ngClass]="!selectedStatus() ? 'btn-neutral' : 'btn-ghost'"
            >
              Todos
            </button>
            <button
              (click)="setStatusFilter('PENDING')"
              class="btn btn-xs"
              [ngClass]="selectedStatus() === 'PENDING' ? 'btn-neutral' : 'btn-ghost'"
            >
              Pendentes
            </button>
            <button
              (click)="setStatusFilter('IN_REVIEW')"
              class="btn btn-xs"
              [ngClass]="selectedStatus() === 'IN_REVIEW' ? 'btn-warning text-warning-content' : 'btn-ghost'"
            >
              Em Revisão
            </button>
            <button
              (click)="setStatusFilter('ONBOARDING_COMPLETED')"
              class="btn btn-xs"
              [ngClass]="selectedStatus() === 'ONBOARDING_COMPLETED' ? 'btn-success text-success-content' : 'btn-ghost'"
            >
              Concluídos (RN-15)
            </button>
          </div>
        </div>
      </div>

      <!-- Personas Table -->
      <div class="card bg-base-100 border border-base-200 shadow-xs overflow-hidden">
        <div class="overflow-x-auto">
          <table class="table table-zebra table-hover w-full text-sm">
            <thead>
              <tr class="bg-base-200/50 text-base-content/70">
                <th>Titular / Nome</th>
                <th>CPF</th>
                <th>Contato</th>
                <th>Status do Onboarding</th>
                <th>Documentos Solicitados</th>
                <th>Data Criação</th>
                <th class="text-right">Ações</th>
              </tr>
            </thead>
            <tbody>
              @if (loading()) {
                <tr>
                  <td colspan="7" class="text-center py-10">
                    <span class="loading loading-spinner loading-md text-primary"></span>
                    <p class="text-xs text-base-content/60 mt-2">Carregando personas...</p>
                  </td>
                </tr>
              } @else if (paginatedPersonas().length === 0) {
                <tr>
                  <td colspan="7" class="text-center py-12">
                    <div class="flex flex-col items-center justify-center space-y-2">
                      <svg xmlns="http://www.w3.org/2000/svg" class="h-10 w-10 text-base-content/30" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                      </svg>
                      <span class="text-sm font-semibold text-base-content/70">Nenhuma persona encontrada</span>
                      <p class="text-xs text-base-content/50">Crie uma nova persona ou ajuste os filtros acima.</p>
                    </div>
                  </td>
                </tr>
              } @else {
                @for (persona of paginatedPersonas(); track persona.id) {
                  <tr class="hover:bg-base-200/40 transition-colors">
                    <td>
                      <div class="font-bold text-base-content">{{ persona.name }}</div>
                      <div class="text-[11px] text-base-content/50 font-mono">{{ persona.id }}</div>
                    </td>
                    <td>
                      <span class="font-mono text-xs">{{ persona.cpf ? formatCpf(persona.cpf) : 'Não informado' }}</span>
                    </td>
                    <td>
                      <div class="text-xs">{{ persona.email || '—' }}</div>
                      <div class="text-[11px] text-base-content/50">{{ persona.phone ? formatPhone(persona.phone) : '—' }}</div>
                    </td>
                    <td>
                      @switch (persona.status) {
                        @case ('ONBOARDING_COMPLETED') {
                          <span class="badge badge-success badge-sm gap-1">
                            <span class="w-1.5 h-1.5 rounded-full bg-success-content"></span>
                            Concluído
                          </span>
                        }
                        @case ('IN_REVIEW') {
                          <span class="badge badge-warning badge-sm gap-1 animate-pulse">
                            <span class="w-1.5 h-1.5 rounded-full bg-warning-content"></span>
                            Em Revisão
                          </span>
                        }
                        @case ('DOCUMENTS_RECEIVED') {
                          <span class="badge badge-info badge-sm gap-1">
                            <span class="w-1.5 h-1.5 rounded-full bg-info-content"></span>
                            Recebido
                          </span>
                        }
                        @default {
                          <span class="badge badge-ghost badge-sm gap-1">
                            <span class="w-1.5 h-1.5 rounded-full bg-base-content/40"></span>
                            Pendente
                          </span>
                        }
                      }
                    </td>
                    <td>
                      <div class="flex flex-wrap gap-1">
                        @for (docType of persona.required_document_types; track docType) {
                          <span class="badge badge-outline badge-xs font-semibold">{{ docType }}</span>
                        }
                      </div>
                    </td>
                    <td class="text-xs text-base-content/60">
                      {{ persona.created_at | date: 'dd/MM/yyyy HH:mm' }}
                    </td>
                    <td class="text-right">
                      <div class="flex justify-end gap-1.5">
                        <button
                          (click)="generateCollectionLink(persona)"
                          class="btn btn-outline btn-xs btn-primary tooltip"
                          data-tip="Gerar Link de Coleta (48h)"
                        >
                          <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                          </svg>
                          Link
                        </button>
                        <a
                          [routerLink]="['/personas', persona.id]"
                          class="btn btn-neutral btn-xs"
                        >
                          Detalhes
                        </a>
                        <button
                          (click)="confirmDelete(persona)"
                          class="btn btn-ghost btn-xs text-error hover:bg-error/10"
                          title="Excluir Persona (RN-13)"
                        >
                          <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                          </svg>
                        </button>
                      </div>
                    </td>
                  </tr>
                }
              }
            </tbody>
          </table>
        </div>

        <!-- Pagination Bar -->
        @if (filteredPersonas().length > 0) {
          <div class="p-3 border-t border-base-200 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-base-content/70">
            <div>
              Exibindo
              <strong class="text-base-content">{{ paginationStart }}</strong> a
              <strong class="text-base-content">{{ paginationEnd }}</strong> de
              <strong class="text-base-content">{{ filteredPersonas().length }}</strong> personas
            </div>

            <div class="join">
              <button
                class="join-item btn btn-xs"
                [disabled]="currentPage() === 1"
                (click)="prevPage()"
              >
                « Anterior
              </button>
              <button class="join-item btn btn-xs btn-active pointer-events-none">
                Pág. {{ currentPage() }} / {{ totalPages() }}
              </button>
              <button
                class="join-item btn btn-xs"
                [disabled]="currentPage() >= totalPages()"
                (click)="nextPage()"
              >
                Próxima »
              </button>
            </div>
          </div>
        }
      </div>
    </div>

    <!-- Modal Nova Persona -->
    @if (isCreateModalOpen()) {
      <div class="modal modal-open">
        <div class="modal-box max-w-lg">
          <h3 class="font-bold text-lg text-base-content mb-4">Cadastrar Nova Persona</h3>

          <form (ngSubmit)="submitCreatePersona()" class="space-y-3">
            <div class="form-control">
              <label class="label py-1"><span class="label-text text-xs font-semibold">Nome Completo *</span></label>
              <input
                type="text"
                [(ngModel)]="newPersona.name"
                name="name"
                placeholder="Ex: Carlos Alberto Ferreira"
                required
                class="input input-bordered input-sm w-full"
              />
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div class="form-control">
                <label class="label py-1"><span class="label-text text-xs font-semibold">CPF</span></label>
                <input
                  type="text"
                  [ngModel]="newPersona.cpf"
                  (input)="onCpfInput($event)"
                  name="cpf"
                  maxlength="14"
                  placeholder="000.000.000-00"
                  class="input input-bordered input-sm w-full font-mono"
                  [ngClass]="{ 'input-error': isCpfInvalid }"
                />
                @if (isCpfInvalid) {
                  <span class="text-[11px] text-error mt-0.5">CPF inválido (dígito verificador incorreto).</span>
                }
              </div>

              <div class="form-control">
                <label class="label py-1"><span class="label-text text-xs font-semibold">Telefone</span></label>
                <input
                  type="text"
                  [ngModel]="newPersona.phone"
                  (input)="onPhoneInput($event)"
                  name="phone"
                  maxlength="15"
                  placeholder="(11) 99999-8888"
                  class="input input-bordered input-sm w-full font-mono"
                  [ngClass]="{ 'input-error': isPhoneInvalid }"
                />
                @if (isPhoneInvalid) {
                  <span class="text-[11px] text-error mt-0.5">Telefone deve conter DDD + número.</span>
                }
              </div>
            </div>

            <div class="form-control">
              <label class="label py-1"><span class="label-text text-xs font-semibold">E-mail</span></label>
              <input
                type="email"
                [(ngModel)]="newPersona.email"
                name="email"
                placeholder="carlos.ferreira@example.com"
                class="input input-bordered input-sm w-full"
                [ngClass]="{ 'input-error': isEmailInvalid }"
              />
              @if (isEmailInvalid) {
                <span class="text-[11px] text-error mt-0.5">E-mail em formato inválido.</span>
              }
            </div>

            <div class="form-control">
              <label class="label py-1">
                <span class="label-text text-xs font-semibold">Documentos Requeridos para Onboarding</span>
              </label>
              <div class="flex gap-4 p-2 bg-base-200/50 rounded-lg">
                <label class="label cursor-pointer gap-2 py-0">
                  <input
                    type="checkbox"
                    [checked]="hasRequiredType('CIN')"
                    (change)="toggleRequiredType('CIN')"
                    class="checkbox checkbox-primary checkbox-sm"
                  />
                  <span class="label-text text-xs font-medium">CIN (Nova Identidade)</span>
                </label>
                <label class="label cursor-pointer gap-2 py-0">
                  <input
                    type="checkbox"
                    [checked]="hasRequiredType('RG_ANTIGO')"
                    (change)="toggleRequiredType('RG_ANTIGO')"
                    class="checkbox checkbox-primary checkbox-sm"
                  />
                  <span class="label-text text-xs font-medium">RG Clássico</span>
                </label>
              </div>
            </div>

            <div class="modal-action mt-6">
              <button type="button" (click)="closeCreateModal()" class="btn btn-ghost btn-sm" [disabled]="submitting()">
                Cancelar
              </button>
              <button type="submit" class="btn btn-primary btn-sm" [disabled]="isFormInvalid || submitting()">
                @if (submitting()) {
                  <span class="loading loading-spinner loading-xs"></span>
                }
                Criar Persona
              </button>
            </div>
          </form>
        </div>
      </div>
    }

    <!-- Modal Link de Coleta Gerado -->
    @if (generatedLink()) {
      <div class="modal modal-open">
        <div class="modal-box max-w-lg">
          <div class="flex items-center space-x-2 text-success mb-3">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <h3 class="font-bold text-lg text-base-content">Link de Coleta Criado!</h3>
          </div>

          <p class="text-xs text-base-content/70 mb-4 leading-relaxed">
            Este link é efêmero e expira em 48 horas (RN-12). O cliente poderá acessar pelo celular e fotografar seus documentos diretamente.
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

          <div class="flex justify-between items-center text-[11px] text-base-content/60 mb-4">
            <span>Expira em: <strong>{{ generatedLink()?.expires_at | date: 'dd/MM/yyyy HH:mm' }}</strong></span>
            <a
              [href]="clientUploadUrl"
              target="_blank"
              class="link link-primary font-medium flex items-center gap-1"
            >
              Abrir como Cliente
              <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
              </svg>
            </a>
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
export class PersonaListComponent implements OnInit {
  private personaService = inject(PersonaService);
  private notificationService = inject(NotificationService);
  private toastService = inject(ToastService);

  public personas = signal<Persona[]>([]);
  public loading = signal<boolean>(false);
  public submitting = signal<boolean>(false);
  public isCreateModalOpen = signal<boolean>(false);
  public generatedLink = signal<CollectionLinkResponse | null>(null);

  // Search & Pagination Signals
  public searchQuery = signal<string>('');
  public selectedStatus = signal<PersonaStatus | undefined>(undefined);
  public currentPage = signal<number>(1);
  public pageSize = signal<number>(10);

  public newPersona: PersonaCreate = {
    name: '',
    email: '',
    cpf: '',
    phone: '',
    required_document_types: ['CIN'],
    metadata_info: {},
  };

  // Reusable format utilities exposed to template
  public formatCpf = formatCpf;
  public formatPhone = formatPhone;

  // Reactive client-side filtering + search
  public filteredPersonas = computed(() => {
    let list = this.personas();
    const query = this.searchQuery().trim().toLowerCase();
    const status = this.selectedStatus();

    if (status) {
      list = list.filter((p) => p.status === status);
    }

    if (query) {
      list = list.filter((p) => {
        const nameMatch = (p.name || '').toLowerCase().includes(query);
        const cpfMatch = (p.cpf || '').replace(/\D/g, '').includes(query.replace(/\D/g, '')) || (p.cpf || '').toLowerCase().includes(query);
        const emailMatch = (p.email || '').toLowerCase().includes(query);
        const phoneMatch = (p.phone || '').replace(/\D/g, '').includes(query.replace(/\D/g, ''));
        const idMatch = (p.id || '').toLowerCase().includes(query);
        return nameMatch || cpfMatch || emailMatch || phoneMatch || idMatch;
      });
    }

    return list;
  });

  public totalPages = computed(() => {
    const total = this.filteredPersonas().length;
    return Math.max(1, Math.ceil(total / this.pageSize()));
  });

  public paginatedPersonas = computed(() => {
    const list = this.filteredPersonas();
    const page = this.currentPage();
    const size = this.pageSize();
    const start = (page - 1) * size;
    return list.slice(start, start + size);
  });

  public get paginationStart(): number {
    if (this.filteredPersonas().length === 0) return 0;
    return (this.currentPage() - 1) * this.pageSize() + 1;
  }

  public get paginationEnd(): number {
    return Math.min(this.currentPage() * this.pageSize(), this.filteredPersonas().length);
  }

  constructor() {
    // Automatically refresh on SSE events that change persona or document states
    effect(() => {
      const event = this.notificationService.latestEvent();
      if (event && (event.event.startsWith('document.') || event.event.startsWith('persona.'))) {
        this.loadPersonas(false);
      }
    });
  }

  public ngOnInit(): void {
    this.loadPersonas();
  }

  public get clientUploadUrl(): string {
    const link = this.generatedLink();
    if (!link) return '';
    const token = link.token || link.public_token || '';
    const origin = window.location.origin;
    return `${origin}/public/upload?token=${encodeURIComponent(token)}`;
  }

  public onSearchChange(query: string): void {
    this.searchQuery.set(query);
    this.currentPage.set(1); // Reset page to 1 on search
  }

  public clearSearch(): void {
    this.searchQuery.set('');
    this.currentPage.set(1);
  }

  public setStatusFilter(status?: PersonaStatus): void {
    this.selectedStatus.set(status);
    this.currentPage.set(1);
  }

  public prevPage(): void {
    if (this.currentPage() > 1) {
      this.currentPage.update((p) => p - 1);
    }
  }

  public nextPage(): void {
    if (this.currentPage() < this.totalPages()) {
      this.currentPage.update((p) => p + 1);
    }
  }

  public loadPersonas(showLoading = true): void {
    if (showLoading) this.loading.set(true);

    this.personaService.list().subscribe({
      next: (data) => {
        this.personas.set(data);
        this.loading.set(false);
      },
      error: () => {
        this.loading.set(false);
      },
    });
  }

  public openCreateModal(): void {
    this.newPersona = {
      name: '',
      email: '',
      cpf: '',
      phone: '',
      required_document_types: ['CIN'],
      metadata_info: {},
    };
    this.isCreateModalOpen.set(true);
  }

  public closeCreateModal(): void {
    this.isCreateModalOpen.set(false);
  }

  public onCpfInput(event: any): void {
    const val = event.target?.value || '';
    this.newPersona.cpf = formatCpf(val);
  }

  public onPhoneInput(event: any): void {
    const val = event.target?.value || '';
    this.newPersona.phone = formatPhone(val);
  }

  public get isCpfInvalid(): boolean {
    if (!this.newPersona.cpf) return false;
    return !validateCpf(this.newPersona.cpf);
  }

  public get isPhoneInvalid(): boolean {
    if (!this.newPersona.phone) return false;
    return !validatePhone(this.newPersona.phone);
  }

  public get isEmailInvalid(): boolean {
    if (!this.newPersona.email) return false;
    return !validateEmail(this.newPersona.email);
  }

  public get isFormInvalid(): boolean {
    if (!this.newPersona.name || !this.newPersona.name.trim()) return true;
    if (this.isCpfInvalid) return true;
    if (this.isPhoneInvalid) return true;
    if (this.isEmailInvalid) return true;
    return false;
  }

  public hasRequiredType(type: string): boolean {
    return (this.newPersona.required_document_types || []).includes(type);
  }

  public toggleRequiredType(type: string): void {
    const list = this.newPersona.required_document_types || [];
    if (list.includes(type)) {
      this.newPersona.required_document_types = list.filter((t) => t !== type);
    } else {
      this.newPersona.required_document_types = [...list, type];
    }
  }

  public submitCreatePersona(): void {
    if (this.isFormInvalid) return;
    this.submitting.set(true);

    const payload: PersonaCreate = {
      ...this.newPersona,
      name: this.newPersona.name.trim(),
      email: this.newPersona.email ? this.newPersona.email.trim() : undefined,
      cpf: this.newPersona.cpf ? this.newPersona.cpf.replace(/\D/g, '') : undefined,
      phone: this.newPersona.phone ? this.newPersona.phone.trim() : undefined,
    };

    this.personaService.create(payload).subscribe({
      next: (created) => {
        this.submitting.set(false);
        this.toastService.success(`Persona '${created.name}' criada com sucesso!`);
        this.closeCreateModal();
        this.loadPersonas();
      },
      error: () => {
        this.submitting.set(false);
      },
    });
  }

  public generateCollectionLink(persona: Persona): void {
    this.personaService.createCollectionLink(persona.id).subscribe({
      next: (resp) => {
        this.generatedLink.set(resp);
      },
      error: () => {
        this.toastService.error('Erro ao gerar link de coleta efêmero.');
      },
    });
  }

  public copyLinkToClipboard(): void {
    if (!this.clientUploadUrl) return;
    navigator.clipboard.writeText(this.clientUploadUrl).then(() => {
      this.toastService.info('Link copiado para a área de transferência!');
    });
  }

  public confirmDelete(persona: Persona): void {
    const msg = `ATENÇÃO (RN-13 Direito ao Esquecimento):\n\nDeseja realmente excluir a Persona '${persona.name}'?\nEsta ação é irreversível e executará a remoção definitiva (Hard Delete) de todos os documentos no PostgreSQL e no bucket do MinIO S3.`;
    if (confirm(msg)) {
      this.personaService.delete(persona.id).subscribe({
        next: () => {
          this.toastService.success(`Persona '${persona.name}' e seus documentos foram excluídos.`);
          this.loadPersonas();
        },
      });
    }
  }
}
