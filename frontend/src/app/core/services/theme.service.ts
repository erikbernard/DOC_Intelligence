import { Injectable, effect, signal } from '@angular/core';

export type AppTheme = 'dark' | 'light';

@Injectable({
  providedIn: 'root',
})
export class ThemeService {
  public currentTheme = signal<AppTheme>(this.getInitialTheme());

  constructor() {
    const initial = this.getInitialTheme();
    if (typeof document !== 'undefined') {
      document.documentElement.setAttribute('data-theme', initial);
    }

    effect(() => {
      const theme = this.currentTheme();
      if (typeof document !== 'undefined') {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('docintelligence_theme', theme);
      }
    });
  }

  private getInitialTheme(): AppTheme {
    if (typeof localStorage !== 'undefined') {
      const saved = localStorage.getItem('docintelligence_theme') as AppTheme;
      if (saved === 'dark' || saved === 'light') {
        return saved;
      }
    }
    return 'dark'; // Default dark theme
  }

  public toggleTheme(): void {
    const next = this.currentTheme() === 'dark' ? 'light' : 'dark';
    if (typeof document !== 'undefined') {
      document.documentElement.setAttribute('data-theme', next);
      localStorage.setItem('docintelligence_theme', next);
    }
    this.currentTheme.set(next);
  }

  public setTheme(theme: AppTheme): void {
    if (typeof document !== 'undefined') {
      document.documentElement.setAttribute('data-theme', theme);
      localStorage.setItem('docintelligence_theme', theme);
    }
    this.currentTheme.set(theme);
  }
}
