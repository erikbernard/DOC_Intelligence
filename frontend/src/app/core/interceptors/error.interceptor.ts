import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { catchError, throwError } from 'rxjs';
import { AuthService } from '../services/auth.service';
import { ToastService } from '../services/toast.service';

export const errorInterceptor: HttpInterceptorFn = (req, next) => {
  const authService = inject(AuthService);
  const toastService = inject(ToastService);

  return next(req).pipe(
    catchError((error: HttpErrorResponse) => {
      let errorMessage = 'Ocorreu um erro inesperado na comunicação com o servidor.';

      if (error.error && typeof error.error === 'object' && error.error.detail) {
        if (typeof error.error.detail === 'string') {
          errorMessage = error.error.detail;
        } else if (Array.isArray(error.error.detail)) {
          // FastAPI validation errors format
          errorMessage = error.error.detail
            .map((d: any) => d.msg || 'Dado inválido')
            .join('; ');
        }
      } else if (error.status === 0) {
        errorMessage = 'Não foi possível conectar ao servidor. Verifique sua conexão ou se a API está ativa.';
      }

      if (error.status === 401 && !req.url.includes('/auth/login')) {
        toastService.warning('Sua sessão expirou. Por favor, faça login novamente.');
        authService.logout();
      } else if (error.status === 403) {
        toastService.error(errorMessage || 'Você não tem permissão para realizar esta operação (RN-10).');
      } else if (error.status === 409) {
        toastService.warning(errorMessage || 'Conflito de edição concorrente detectado (RN-07).');
      } else {
        toastService.error(errorMessage);
      }

      return throwError(() => error);
    })
  );
};
