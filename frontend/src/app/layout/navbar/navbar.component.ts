import { Component, HostListener, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule } from '@angular/router';
import { AuthService } from '../../core/services/auth.service';
import { NotificationService } from '../../core/services/notification.service';
import { ThemeService } from '../../core/services/theme.service';

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
        <!-- Theme Toggle Button (Light / Dark) -->
        <button
          type="button"
          (click)="onThemeClick($event)"
          class="btn btn-ghost btn-circle"
          [attr.aria-label]="themeService.currentTheme() === 'dark' ? 'Mudar para tema claro' : 'Mudar para tema escuro'"
          [title]="themeService.currentTheme() === 'dark' ? 'Mudar para tema Claro' : 'Mudar para tema Escuro'"
        >
          @if (themeService.currentTheme() === 'dark') {
            <!-- Sun Icon for switching to light -->
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-warning" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
            </svg>
          } @else {
            <!-- Moon Icon for switching to dark -->
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-base-content" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
            </svg>
          }
        </button>

        <!-- Notification Dropdown with Real-Time Badge -->
        <div class="dropdown dropdown-end" [class.dropdown-open]="isNotificationsOpen()">
          <button
            type="button"
            (click)="toggleNotifications($event)"
            class="btn btn-ghost btn-circle relative"
            aria-label="Notificações"
            title="Notificações"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-base-content" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
            </svg>
            @if (notificationService.unreadCount() > 0) {
              <span class="badge badge-xs badge-error indicator-item absolute top-2 right-2 p-1 font-bold text-[10px]">
                {{ notificationService.unreadCount() }}
              </span>
            }
          </button>

          <!-- Dropdown content: Clean custom container without .menu to prevent visual breakage -->
          @if (isNotificationsOpen()) {
            <div
              (click)="$event.stopPropagation()"
              class="dropdown-content z-50 p-4 shadow-2xl bg-base-100 rounded-2xl w-80 sm:w-96 border border-base-200 max-h-[30rem] flex flex-col mt-2"
            >
              <div class="flex justify-between items-center pb-3 border-b border-base-200">
                <div class="flex items-center space-x-2">
                  <span class="font-bold text-sm text-base-content">Notificações em Tempo Real</span>
                  @if (notificationService.unreadCount() > 0) {
                    <span class="badge badge-primary badge-sm font-semibold">{{ notificationService.unreadCount() }} novas</span>
                  }
                </div>
                <button
                  type="button"
                  (click)="notificationService.markAllAsRead()"
                  class="btn btn-ghost btn-xs text-primary font-medium"
                  [disabled]="notificationService.unreadCount() === 0"
                >
                  Marcar lidas
                </button>
              </div>

              <!-- List of events -->
              <div class="overflow-y-auto flex-1 my-2 space-y-2 pr-1">
                @if (notificationService.notifications().length === 0) {
                  <div class="py-8 text-center text-sm text-base-content/60 flex flex-col items-center justify-center space-y-2">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 text-base-content/30" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                    </svg>
                    <span>Nenhuma notificação recebida até o momento.</span>
                  </div>
                } @else {
                  @for (item of notificationService.notifications(); track item.id) {
                    <div
                      class="p-3 rounded-xl hover:bg-base-200/80 cursor-pointer transition-all duration-150 border border-base-200 shadow-xs"
                      [ngClass]="{ 'bg-primary/5 border-primary/20': !item.read, 'bg-base-100': item.read }"
                      (click)="onNotificationClick(item, $event)"
                    >
                      <div class="flex justify-between items-start gap-2">
                        <div class="flex items-center gap-1.5 min-w-0">
                          @if (!item.read) {
                            <span class="w-2 h-2 rounded-full bg-primary shrink-0"></span>
                          }
                          <span class="font-bold text-xs text-base-content truncate">{{ item.title }}</span>
                        </div>
                        <span class="text-[10px] text-base-content/50 shrink-0 font-mono">{{ item.timestamp | date: 'HH:mm:ss' }}</span>
                      </div>
                      <p class="text-xs text-base-content/80 mt-1 line-clamp-2 leading-relaxed">{{ item.message }}</p>
                      <div class="flex justify-end items-center mt-2 pt-1.5 border-t border-base-200/40">
                        <span class="text-[11px] font-semibold text-primary flex items-center gap-1 hover:underline">
                          {{ item.documentId ? 'Conferir Documento' : 'Ver Detalhes da Persona' }}
                          <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5 inline" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                          </svg>
                        </span>
                      </div>
                    </div>
                  }
                }
              </div>

              @if (notificationService.notifications().length > 0) {
                <div class="pt-2 border-t border-base-200 text-center">
                  <button type="button" (click)="notificationService.clearAll()" class="btn btn-ghost btn-xs text-error">
                    Limpar Histórico
                  </button>
                </div>
              }
            </div>
          }
        </div>

        <!-- User Profile Dropdown -->
        <div class="dropdown dropdown-end" [class.dropdown-open]="isProfileOpen()">
          <button
            type="button"
            (click)="toggleProfile($event)"
            class="btn btn-ghost btn-sm flex items-center space-x-2"
          >
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

          @if (isProfileOpen()) {
            <ul
              (click)="$event.stopPropagation()"
              class="dropdown-content z-50 menu p-2 shadow-xl bg-base-100 rounded-box w-52 border border-base-200 mt-2"
            >
              <li class="menu-title px-4 py-1 text-xs text-base-content/60">
                {{ authService.currentUser()?.email }}
              </li>
              <li>
                <a (click)="onLogout()" class="text-error font-medium cursor-pointer">
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                  </svg>
                  Encerrar Sessão
                </a>
              </li>
            </ul>
          }
        </div>
      </div>
    </header>
  `,
})
export class NavbarComponent {
  public authService = inject(AuthService);
  public notificationService = inject(NotificationService);
  public themeService = inject(ThemeService);
  private router = inject(Router);

  public isNotificationsOpen = signal<boolean>(false);
  public isProfileOpen = signal<boolean>(false);

  @HostListener('document:click')
  public onDocumentClick(): void {
    this.isNotificationsOpen.set(false);
    this.isProfileOpen.set(false);
  }

  public get userInitials(): string {
    const name = this.authService.currentUser()?.full_name || 'Doc Intel';
    return name
      .split(' ')
      .slice(0, 2)
      .map((part) => part[0])
      .join('');
  }

  public onThemeClick(event: Event): void {
    event.stopPropagation();
    this.themeService.toggleTheme();
  }

  public toggleNotifications(event: Event): void {
    event.stopPropagation();
    this.isNotificationsOpen.update((open) => !open);
    this.isProfileOpen.set(false);
  }

  public toggleProfile(event: Event): void {
    event.stopPropagation();
    this.isProfileOpen.update((open) => !open);
    this.isNotificationsOpen.set(false);
  }

  public onNotificationClick(item: any, event?: Event): void {
    if (event) {
      event.stopPropagation();
    }
    this.notificationService.markAsRead(item.id);
    this.isNotificationsOpen.set(false);

    // Prioritize direct navigation to document review / split-screen conference
    if (item.documentId) {
      this.router.navigateByUrl(`/documents/${item.documentId}/review`);
    } else if (item.link && item.link.includes('/documents/')) {
      this.router.navigateByUrl(item.link);
    } else if (item.personaId) {
      this.router.navigateByUrl(`/personas/${item.personaId}`);
    } else if (item.link) {
      this.router.navigateByUrl(item.link);
    }
  }

  public onLogout(): void {
    this.isProfileOpen.set(false);
    this.authService.logout();
  }
}
