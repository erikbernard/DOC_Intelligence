import { Component, EventEmitter, Input, Output } from '@angular/core';
import { CommonModule } from '@angular/common';

export interface TemplateOption {
  code: string;
  title: string;
  subtitle: string;
  badge?: string;
  icon: string;
}

@Component({
  selector: 'app-template-card',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full">
      @for (opt of options; track opt.code) {
        <div
          (click)="select(opt.code)"
          class="card border-2 cursor-pointer transition-all duration-200 p-4 rounded-xl flex flex-row items-center space-x-3 select-none"
          [ngClass]="
            selectedCode === opt.code
              ? 'border-primary bg-primary/5 shadow-md ring-1 ring-primary/30'
              : 'border-base-300 bg-base-100 hover:border-base-content/30'
          "
        >
          <!-- Icon -->
          <div
            class="w-12 h-12 rounded-xl flex items-center justify-center shrink-0"
            [ngClass]="selectedCode === opt.code ? 'bg-primary text-primary-content' : 'bg-base-200 text-base-content'"
          >
            @if (opt.code === 'CIN') {
              <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V8a2 2 0 00-2-2h-5m-4 0V5a2 2 0 114 0v1m-4 0a2 2 0 104 0m-5 8a2 2 0 100-4 2 2 0 000 4zm0 0c1.306 0 2.417.835 2.83 2M9 14a3.001 3.001 0 00-2.83 2M15 11h3m-3 4h2" />
              </svg>
            } @else {
              <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            }
          </div>

          <!-- Text info -->
          <div class="flex-1 min-w-0">
            <div class="flex items-center space-x-2">
              <span class="font-bold text-xs text-base-content truncate">{{ opt.title }}</span>
              @if (opt.badge) {
                <span class="badge badge-primary badge-xs font-semibold">{{ opt.badge }}</span>
              }
            </div>
            <p class="text-[11px] text-base-content/60 mt-0.5 line-clamp-2 leading-tight">
              {{ opt.subtitle }}
            </p>
          </div>

          <!-- Radio Indicator -->
          <div class="shrink-0">
            <input
              type="radio"
              [checked]="selectedCode === opt.code"
              class="radio radio-primary radio-sm"
              readonly
            />
          </div>
        </div>
      }
    </div>
  `,
})
export class TemplateCardComponent {
  @Input() selectedCode: string = 'CIN';
  @Output() selected = new EventEmitter<string>();

  public options: TemplateOption[] = [
    {
      code: 'CIN',
      title: 'CIN (Nova Identidade)',
      subtitle: 'Carteira de Identidade Nacional unificada pelo CPF.',
      badge: 'Recomendada',
      icon: 'cin',
    },
    {
      code: 'RG_ANTIGO',
      title: 'RG Tradicional',
      subtitle: 'Carteira de identidade estadual física (modelo clássico).',
      icon: 'rg',
    },
  ];

  public select(code: string): void {
    this.selected.emit(code);
  }
}
