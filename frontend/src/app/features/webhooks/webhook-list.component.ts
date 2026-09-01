import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { WebhookService } from '../../core/services/webhook.service';
import { ToastService } from '../../core/services/toast.service';
import { WebhookConfig, WebhookCreate, WebhookDeliveryLog } from '../../core/models/webhook.model';

@Component({
  selector: 'app-webhook-list',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="space-y-6">
      <!-- Top Title Bar -->
      <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-base-100 p-5 rounded-2xl border border-base-200 shadow-xs">
        <div>
          <h1 class="text-2xl font-bold text-base-content">Webhooks & Integrações</h1>
          <p class="text-sm text-base-content/60 mt-0.5">
            Configure endpoints externos para receber eventos do ciclo de vida dos documentos.
          </p>
        </div>
        <button (click)="openCreateModal()" class="btn btn-primary btn-sm sm:btn-md gap-2 shadow-sm">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
          </svg>
          Novo Webhook
        </button>
      </div>

      <!-- Webhooks Table -->
      <div class="card bg-base-100 border border-base-200 shadow-xs overflow-hidden">
        <div class="overflow-x-auto">
          <table class="table table-zebra w-full text-sm">
            <thead>
              <tr class="bg-base-200/50 text-base-content/70 text-xs">
                <th>URL de Destino</th>
                <th>Eventos Inscritos</th>
                <th>Status</th>
                <th>Chave Secreta</th>
                <th>Criado em</th>
                <th class="text-right">Ações</th>
              </tr>
            </thead>
            <tbody>
              @if (loading()) {
                <tr>
                  <td colspan="6" class="text-center py-8">
                    <span class="loading loading-spinner loading-md text-primary"></span>
                  </td>
                </tr>
              } @else if (webhooks().length === 0) {
                <tr>
                  <td colspan="6" class="text-center py-10 text-base-content/60">
                    Nenhum webhook cadastrado. Adicione um endpoint para receber notificações de OCR em tempo real.
                  </td>
                </tr>
              } @else {
                @for (item of webhooks(); track item.id) {
                  <tr class="hover:bg-base-200/40">
                    <td>
                      <span class="font-mono text-xs font-semibold text-primary">{{ item.target_url }}</span>
                    </td>
                    <td>
                      <div class="flex flex-wrap gap-1">
                        @for (ev of item.events; track ev) {
                          <span class="badge badge-outline badge-xs font-mono">{{ ev }}</span>
                        }
                      </div>
                    </td>
                    <td>
                      <span
                        class="badge badge-sm"
                        [ngClass]="item.is_active ? 'badge-success' : 'badge-ghost'"
                      >
                        {{ item.is_active ? 'Ativo' : 'Inativo' }}
                      </span>
                    </td>
                    <td>
                      <span class="text-xs text-base-content/50 font-mono">
                        {{ item.secret_token ? '••••••••' : 'Nenhuma' }}
                      </span>
                    </td>
                    <td class="text-xs text-base-content/60">
                      {{ item.created_at | date: 'dd/MM/yyyy HH:mm' }}
                    </td>
                    <td class="text-right">
                      <div class="flex justify-end gap-2">
                        <button (click)="viewLogs(item)" class="btn btn-ghost btn-xs">
                          Logs
                        </button>
                        <button (click)="deleteWebhook(item)" class="btn btn-ghost btn-xs text-error">
                          Excluir
                        </button>
                      </div>
                    </td>
                  </tr>
                }
              }
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Modal Novo Webhook -->
    @if (isCreateModalOpen()) {
      <div class="modal modal-open">
        <div class="modal-box max-w-lg">
          <h3 class="font-bold text-lg text-base-content mb-3">Cadastrar Webhook</h3>

          <form (ngSubmit)="submitCreateWebhook()" class="space-y-4">
            <div class="form-control">
              <label class="label py-1"><span class="label-text text-xs font-semibold">URL de Destino (HTTPS) *</span></label>
              <input
                type="url"
                [(ngModel)]="newWebhook.target_url"
                name="target_url"
                placeholder="https://sua-empresa.com/api/webhooks/doc-intelligence"
                required
                class="input input-bordered input-sm w-full font-mono text-xs"
              />
            </div>

            <div class="form-control">
              <label class="label py-1"><span class="label-text text-xs font-semibold">Chave Secreta (Opcional - Assinatura HMAC)</span></label>
              <input
                type="text"
                [(ngModel)]="newWebhook.secret_token"
                name="secret_token"
                placeholder="whsec_..."
                class="input input-bordered input-sm w-full font-mono text-xs"
              />
            </div>

            <div class="form-control">
              <label class="label py-1"><span class="label-text text-xs font-semibold">Eventos para Notificação</span></label>
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-2 p-3 bg-base-200/50 rounded-lg text-xs">
                @for (ev of availableEvents; track ev) {
                  <label class="label cursor-pointer justify-start gap-2 py-1">
                    <input
                      type="checkbox"
                      [checked]="newWebhook.events.includes(ev)"
                      (change)="toggleEvent(ev)"
                      class="checkbox checkbox-primary checkbox-xs"
                    />
                    <span class="label-text font-mono text-xs">{{ ev }}</span>
                  </label>
                }
              </div>
            </div>

            <div class="modal-action mt-6">
              <button type="button" (click)="closeCreateModal()" class="btn btn-ghost btn-sm" [disabled]="submitting()">
                Cancelar
              </button>
              <button type="submit" class="btn btn-primary btn-sm" [disabled]="submitting() || !newWebhook.target_url">
                @if (submitting()) {
                  <span class="loading loading-spinner loading-xs"></span>
                }
                Salvar Webhook
              </button>
            </div>
          </form>
        </div>
      </div>
    }

    <!-- Modal Logs de Entrega -->
    @if (selectedWebhookForLogs()) {
      <div class="modal modal-open">
        <div class="modal-box max-w-xl">
          <h3 class="font-bold text-base text-base-content mb-2">
            Histórico de Entregas: {{ selectedWebhookForLogs()?.target_url }}
          </h3>

          <div class="max-h-80 overflow-y-auto space-y-2 my-4">
            @if (logsLoading()) {
              <div class="text-center py-6">
                <span class="loading loading-spinner loading-md text-primary"></span>
              </div>
            } @else if (deliveryLogs().length === 0) {
              <div class="text-center py-6 text-xs text-base-content/50">
                Nenhum disparo registrado para este webhook ainda.
              </div>
            } @else {
              @for (log of deliveryLogs(); track log.id) {
                <div class="p-2.5 bg-base-200 rounded-lg flex justify-between items-center text-xs">
                  <div>
                    <span class="font-mono font-bold">{{ log.event_name }}</span>
                    <span class="text-base-content/50 block text-[10px]">{{ log.created_at | date: 'dd/MM/yyyy HH:mm:ss' }}</span>
                  </div>
                  <div class="flex items-center space-x-2">
                    <span
                      class="badge badge-sm font-mono"
                      [ngClass]="log.success ? 'badge-success' : 'badge-error'"
                    >
                      HTTP {{ log.status_code }}
                    </span>
                    <span class="text-[10px] text-base-content/50">Tentativas: {{ log.attempt_count }}</span>
                  </div>
                </div>
              }
            }
          </div>

          <div class="modal-action">
            <button (click)="selectedWebhookForLogs.set(null)" class="btn btn-sm btn-neutral">
              Fechar
            </button>
          </div>
        </div>
      </div>
    }
  `,
})
export class WebhookListComponent implements OnInit {
  private webhookService = inject(WebhookService);
  private toastService = inject(ToastService);

  public webhooks = signal<WebhookConfig[]>([]);
  public loading = signal<boolean>(false);
  public submitting = signal<boolean>(false);
  public isCreateModalOpen = signal<boolean>(false);

  public selectedWebhookForLogs = signal<WebhookConfig | null>(null);
  public deliveryLogs = signal<WebhookDeliveryLog[]>([]);
  public logsLoading = signal<boolean>(false);

  public availableEvents = [
    'document.processing',
    'document.ready',
    'document.needs_review',
    'document.rejected',
    'persona.completed',
  ];

  public newWebhook: WebhookCreate = {
    target_url: '',
    secret_token: '',
    events: ['document.ready', 'persona.completed'],
    is_active: true,
  };

  public ngOnInit(): void {
    this.loadWebhooks();
  }

  public loadWebhooks(): void {
    this.loading.set(true);
    this.webhookService.list().subscribe({
      next: (list: WebhookConfig[]) => {
        this.webhooks.set(list);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }

  public openCreateModal(): void {
    this.newWebhook = {
      target_url: '',
      secret_token: '',
      events: ['document.ready', 'persona.completed'],
      is_active: true,
    };
    this.isCreateModalOpen.set(true);
  }

  public closeCreateModal(): void {
    this.isCreateModalOpen.set(false);
  }

  public toggleEvent(ev: string): void {
    if (this.newWebhook.events.includes(ev)) {
      this.newWebhook.events = this.newWebhook.events.filter((e: string) => e !== ev);
    } else {
      this.newWebhook.events = [...this.newWebhook.events, ev];
    }
  }

  public submitCreateWebhook(): void {
    if (!this.newWebhook.target_url) return;
    this.submitting.set(true);

    this.webhookService.create(this.newWebhook).subscribe({
      next: () => {
        this.submitting.set(false);
        this.toastService.success('Webhook cadastrado com sucesso!');
        this.closeCreateModal();
        this.loadWebhooks();
      },
      error: () => this.submitting.set(false),
    });
  }

  public deleteWebhook(item: WebhookConfig): void {
    if (confirm(`Deseja realmente remover o webhook ${item.target_url}?`)) {
      this.webhookService.delete(item.id).subscribe({
        next: () => {
          this.toastService.success('Webhook removido com sucesso.');
          this.loadWebhooks();
        },
      });
    }
  }

  public viewLogs(item: WebhookConfig): void {
    this.selectedWebhookForLogs.set(item);
    this.logsLoading.set(true);
    this.webhookService.getLogs(item.id).subscribe({
      next: (logs: WebhookDeliveryLog[]) => {
        this.deliveryLogs.set(logs);
        this.logsLoading.set(false);
      },
      error: () => this.logsLoading.set(false),
    });
  }
}
