import { Component, EventEmitter, Input, Output } from '@angular/core';
import { CommonModule } from '@angular/common';

export interface StagedDocument {
  id: string;
  file: File;
  previewUrl: string;
  documentType: string;
}

@Component({
  selector: 'app-staged-docs',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="space-y-2">
      <div class="flex justify-between items-center">
        <span class="text-xs font-bold text-base-content/70 uppercase tracking-wider">
          Documentos Prontos para Envio ({{ items.length }})
        </span>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
        @for (item of items; track item.id) {
          <div class="card bg-base-100 border border-base-200 p-2.5 rounded-xl shadow-xs flex flex-row items-center justify-between gap-3">
            <!-- Thumbnail Preview -->
            <div class="w-14 h-14 rounded-lg bg-base-200 overflow-hidden shrink-0 flex items-center justify-center border border-base-300">
              @if (item.file.type.startsWith('image/')) {
                <img [src]="item.previewUrl" alt="Thumbnail" class="w-full h-full object-cover" />
              } @else {
                <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                </svg>
              }
            </div>

            <!-- Details -->
            <div class="flex-1 min-w-0">
              <span class="badge badge-neutral badge-xs font-semibold uppercase">{{ item.documentType }}</span>
              <p class="font-medium text-xs text-base-content truncate mt-0.5">{{ item.file.name }}</p>
              <span class="text-[10px] text-base-content/50 font-mono">
                {{ (item.file.size / 1024).toFixed(0) }} KB
              </span>
            </div>

            <!-- Remove Button -->
            <button
              (click)="remove.emit(item.id)"
              class="btn btn-ghost btn-xs btn-circle text-error hover:bg-error/10 shrink-0"
              title="Remover documento"
            >
              ✕
            </button>
          </div>
        }
      </div>
    </div>
  `,
})
export class StagedDocsComponent {
  @Input() items: StagedDocument[] = [];
  @Output() remove = new EventEmitter<string>();
}
