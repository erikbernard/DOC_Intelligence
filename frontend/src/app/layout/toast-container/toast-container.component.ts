import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ToastService } from '../../core/services/toast.service';

@Component({
  selector: 'app-toast-container',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="toast toast-top toast-end z-50 space-y-2 p-4 max-w-sm w-full">
      @for (toast of toastService.toasts(); track toast.id) {
        <div
          class="alert shadow-lg flex justify-between items-start text-sm transition-all duration-300 transform translate-y-0"
          [ngClass]="{
            'alert-info': toast.type === 'info',
            'alert-success': toast.type === 'success',
            'alert-warning': toast.type === 'warning',
            'alert-error': toast.type === 'error'
          }"
        >
          <div class="flex items-start space-x-2">
            @switch (toast.type) {
              @case ('success') {
                <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-5 w-5 text-success-content" fill="none" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
              }
              @case ('warning') {
                <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-5 w-5 text-warning-content" fill="none" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
              }
              @case ('error') {
                <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-5 w-5 text-error-content" fill="none" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
              }
              @default {
                <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-5 w-5 text-info-content" fill="none" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
              }
            }
            <span class="break-words font-medium leading-tight">{{ toast.message }}</span>
          </div>
          <button (click)="toastService.remove(toast.id)" class="btn btn-ghost btn-xs btn-circle ml-2">
            ✕
          </button>
        </div>
      }
    </div>
  `,
})
export class ToastContainerComponent {
  public toastService = inject(ToastService);
}
