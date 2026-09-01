import { Routes } from '@angular/router';
import { authGuard } from './core/guards/auth.guard';
import { LoginComponent } from './features/auth/login/login.component';
import { ShellComponent } from './layout/shell/shell.component';
import { PersonaListComponent } from './features/personas/persona-list/persona-list.component';
import { PersonaDetailComponent } from './features/personas/persona-detail/persona-detail.component';
import { DocumentReviewComponent } from './features/conference/document-review.component';
import { WebhookListComponent } from './features/webhooks/webhook-list.component';
import { PublicUploadComponent } from './features/public/public-upload.component';

export const routes: Routes = [
  {
    path: 'login',
    component: LoginComponent,
  },
  {
    path: 'public/upload',
    component: PublicUploadComponent,
  },
  {
    path: '',
    component: ShellComponent,
    canActivate: [authGuard],
    children: [
      {
        path: '',
        redirectTo: 'personas',
        pathMatch: 'full',
      },
      {
        path: 'personas',
        component: PersonaListComponent,
      },
      {
        path: 'personas/:id',
        component: PersonaDetailComponent,
      },
      {
        path: 'documents/:id/review',
        component: DocumentReviewComponent,
      },
      {
        path: 'webhooks',
        component: WebhookListComponent,
      },
    ],
  },
  {
    path: '**',
    redirectTo: 'personas',
  },
];
