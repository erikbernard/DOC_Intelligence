import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { NavbarComponent } from '../navbar/navbar.component';
import { SidebarComponent } from '../sidebar/sidebar.component';
import { ToastContainerComponent } from '../toast-container/toast-container.component';

@Component({
  selector: 'app-shell',
  standalone: true,
  imports: [
    CommonModule,
    RouterModule,
    NavbarComponent,
    SidebarComponent,
    ToastContainerComponent,
  ],
  template: `
    <div class="drawer lg:drawer-open min-h-screen bg-base-200/40">
      <input id="main-drawer" type="checkbox" class="drawer-toggle" />

      <!-- Main Page Content -->
      <div class="drawer-content flex flex-col min-h-screen">
        <app-navbar />

        <main class="flex-1 p-4 md:p-6 lg:p-8 max-w-7xl w-full mx-auto">
          <router-outlet />
        </main>
      </div>

      <!-- Drawer Side (Sidebar) -->
      <div class="drawer-side z-40">
        <label for="main-drawer" aria-label="close sidebar" class="drawer-overlay"></label>
        <app-sidebar />
      </div>
    </div>

    <!-- Global Toast Notifications -->
    <app-toast-container />
  `,
})
export class ShellComponent {}
