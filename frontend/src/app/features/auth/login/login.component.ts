import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../../core/services/auth.service';
import { ToastService } from '../../../core/services/toast.service';
import { NotificationService } from '../../../core/services/notification.service';
import { ToastContainerComponent } from '../../../layout/toast-container/toast-container.component';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule, ToastContainerComponent],
  template: `
    <div class="min-h-screen bg-base-200 flex items-center justify-center p-4">
      <div class="card w-full max-w-md bg-base-100 shadow-2xl border border-base-300">
        <div class="card-body p-6 sm:p-8">
          <!-- Logo & Header -->
          <div class="text-center mb-6">
            <div class="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-primary/10 text-primary mb-3">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <h1 class="text-2xl font-bold text-base-content">DOC_Intelligence</h1>
            <p class="text-xs text-base-content/60 mt-1">Plataforma de Onboarding e OCR de Identidades</p>
          </div>

          <!-- Error Alert -->
          @if (errorMessage()) {
            <div class="alert alert-error text-xs p-3 mb-4 rounded-lg">
              <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-4 w-4" fill="none" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
              <span>{{ errorMessage() }}</span>
            </div>
          }

          <form (ngSubmit)="onSubmit()" class="space-y-4">
            <!-- Email -->
            <div class="form-control">
              <label class="label py-1">
                <span class="label-text font-medium text-xs">E-mail de Acesso</span>
              </label>
              <input
                type="email"
                name="email"
                [(ngModel)]="email"
                placeholder="seu.email@empresa.com"
                required
                class="input input-bordered w-full focus:input-primary text-sm"
              />
            </div>

            <!-- Password -->
            <div class="form-control">
              <label class="label py-1">
                <span class="label-text font-medium text-xs">Senha</span>
              </label>
              <input
                type="password"
                name="password"
                [(ngModel)]="password"
                placeholder="••••••••"
                required
                class="input input-bordered w-full focus:input-primary text-sm"
              />
            </div>

            <!-- Submit Button -->
            <button
              type="submit"
              class="btn btn-primary w-full mt-2"
              [disabled]="loading() || !email || !password"
            >
              @if (loading()) {
                <span class="loading loading-spinner loading-sm"></span>
                Autenticando...
              } @else {
                Acessar Plataforma
              }
            </button>
          </form>

          <!-- Quick Fill helper for testing -->
          <div class="divider text-xs text-base-content/40 my-4">Acesso Rápido para Demonstração</div>
          <button
            type="button"
            (click)="fillAdminCredentials()"
            class="btn btn-outline btn-xs w-full text-xs font-normal"
          >
            Preencher com Administrador Padrão
          </button>
        </div>
      </div>
    </div>
    <app-toast-container />
  `,
})
export class LoginComponent {
  private authService = inject(AuthService);
  private notificationService = inject(NotificationService);
  private toastService = inject(ToastService);
  private router = inject(Router);

  public email = 'admin@docintelligence.com';
  public password = 'adminpassword123';
  public loading = signal<boolean>(false);
  public errorMessage = signal<string | null>(null);

  constructor() {
    if (this.authService.isAuthenticated()) {
      this.router.navigate(['/personas']);
    }
  }

  public fillAdminCredentials(): void {
    this.email = 'admin@docintelligence.com';
    this.password = 'adminpassword123';
    this.errorMessage.set(null);
  }

  public onSubmit(): void {
    this.loading.set(true);
    this.errorMessage.set(null);

    this.authService.login(this.email, this.password).subscribe({
      next: () => {
        this.loading.set(false);
        this.toastService.success('Autenticado com sucesso!');
        this.notificationService.connect();
        this.router.navigate(['/personas']);
      },
      error: (err) => {
        this.loading.set(false);
        this.errorMessage.set(
          err.error?.detail || 'Falha ao autenticar. Verifique seu e-mail e senha.'
        );
      },
    });
  }
}
