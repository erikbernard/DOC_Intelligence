import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule } from '@angular/router';
import { AuthService } from '../../core/services/auth.service';
import { NotificationService } from '../../core/services/notification.service';

@Component({
  selector: 'app-navbar',
  standalone: true,
  imports: [CommonModule, RouterModule],
  template: `
    <header class="navbar bg-base-100 border-b border-base-200 px-4 h-16 sticky top-0 z-30 shadow-xs">
      <div class="flex-1 items-center space-x-3">
        <!-- Mobile Sidebar Toggle -->
        <label for="main-drawer" class="btn btn-square btn-ghost lg:hidden">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="inline-block w-5 h-5 stroke-current">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"></path>
          </svg>
        </label>

        <!-- Brand / Title -->
        <div class="flex items-center space-x-2">
          <span class="text-xl font-bold tracking-tight bg-linear-to-r from-primary to-secondary bg-clip-text text-transparent">
            DOC_Intelligence
          </span>
          <span class="badge badge-sm badge-outline font-mono text-xs">CIN/RG MVP</span>
        </div>

        <!-- SSE Connectivity status indicator -->
        <div class="hidden sm:flex items-center space-x-1.5 ml-4 pl-4 border-l border-base-300">
          <span
            class="inline-block w-2.5 h-2.5 rounded-full animate-pulse"
            [ngClass]="notificationService.isConnected() ? 'bg-success' : 'bg-warning'"
          ></span>
          <span class="text-xs text-base-content/70 font-medium">
            {{ notificationService.isConnected() ? 'SSE Conectado' : 'SSE Reconectando...' }}
          </span>
        </div>
      </div>

      <div class="flex-none items-center space-x-2">
        <!-- Notification Dropdown with Real-Time Badge -->
        <div class="dropdown dropdown-end">
          <button tabindex="0" class="btn btn-ghost btn-circle relative" aria-label="Notificações">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-base-content" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
            </svg>
            @if (notificationService.unreadCount() > 0) {
              <span class="badge badge-xs badge-error indicator-item absolute top-2 right-2 p-1 font-bold text-[10px]">
                {{ notificationService.unreadCount() }}
              </span>
            }
          </button>

          <!-- Dropdown content -->
          <div
            tabindex="0"
            class="dropdown-content z-50 menu p-3 shadow-xl bg-base-100 rounded-box w-80 sm:w-96 border border-base-200 max-h-[28rem] flex flex-col"
          >
            <div class="flex justify-between items-center pb-2 border-b border-base-200">
              <div class="flex items-center space-x-2">
                <span class="font-bold text-sm">Notificações em Tempo Real</span>
                @if (notificationService.unreadCount() > 0) {
                  <span class="badge badge-primary badge-sm">{{ notificationService.unreadCount() }} novas</span>
                }
              </div>
              <button
                (click)="notificationService.markAllAsRead()"
                class="btn btn-ghost btn-xs text-primary"
                [disabled]="notificationService.unreadCount() === 0"
              >
                Marcar lidas
              </button>
            </div>

            <!-- List of events -->
            <div class="overflow-y-auto flex-1 my-2 space-y-1.5 divide-y divide-base-200">
              @if (notificationService.notifications().length === 0) {
                <div class="p-4 text-center text-sm text-base-content/60">
                  Nenhuma notificação recebida até o momento.
                </div>
              } @else {
                @for (item of notificationService.notifications(); track item.id) {
                  <div
                    class="p-2 rounded-md hover:bg-base-200 cursor-pointer transition-colors"
                    [ngClass]="{ 'bg-base-200/40': !item.read }"
                    (click)="onNotificationClick(item)"
                  >
                    <div class="flex justify-between items-start">
                      <span class="font-semibold text-xs text-base-content">{{ item.title }}</span>
                      <span class="text-[10px] text-base-content/50">{{ item.timestamp | date: 'HH:mm:ss' }}</span>
                    </div>
                    <p class="text-xs text-base-content/80 mt-0.5 line-clamp-2">{{ item.message }}</p>
                  </div>
                }
              }
            </div>

            @if (notificationService.notifications().length > 0) {
              <div class="pt-2 border-t border-base-200 text-center">
                <button (click)="notificationService.clearAll()" class="btn btn-ghost btn-xs text-error">
                  Limpar Histórico
                </button>
              </div>
            }
          </div>
        </div>

        <!-- User Profile Dropdown -->
        <div class="dropdown dropdown-end">
          <button tabindex="0" class="btn btn-ghost btn-sm flex items-center space-x-2">
            <div class="avatar placeholder">
              <div class="bg-neutral text-neutral-content rounded-full w-8 h-8">
                <span class="text-xs uppercase">{{ userInitials }}</span>
              </div>
            </div>
            <div class="hidden md:flex flex-col items-start text-left">
              <span class="text-xs font-semibold leading-none">{{ authService.currentUser()?.full_name || 'Usuário' }}</span>
              <span class="badge badge-xs badge-neutral mt-0.5">{{ authService.currentUser()?.role || 'OPERADOR' }}</span>
            </div>
          </button>
          <ul tabindex="0" class="dropdown-content z-50 menu p-2 shadow-lg bg-base-100 rounded-box w-52 border border-base-200">
            <li class="menu-title px-4 py-1 text-xs text-base-content/60">
              {{ authService.currentUser()?.email }}
            </li>
            <li>
              <a (click)="authService.logout()" class="text-error font-medium">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                </svg>
                Encerrar Sessão
              </a>
            </li>
          </ul>
        </div>
      </div>
    </header>
  `,
})
export class NavbarComponent {
  public authService = inject(AuthService);
  public notificationService = inject(NotificationService);
  private router = inject(Router);

  public get userInitials(): string {
    const name = this.authService.currentUser()?.full_name || 'Doc Intel';
    return name
      .split(' ')
      .slice(0, 2)
      .map((part) => part[0])
      .join('');
  }

  public onNotificationClick(item: any): void {
    this.notificationService.markAsRead(item.id);
    if (item.link) {
      this.router.navigateByUrl(item.link);
    }
  }
}
