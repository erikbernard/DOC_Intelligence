import {
  Component,
  ElementRef,
  EventEmitter,
  OnDestroy,
  OnInit,
  Output,
  ViewChild,
  signal,
} from '@angular/core';
import { CommonModule } from '@angular/common';

export type CameraFacing = 'environment' | 'user';
export type OverlayOrientation = 'landscape' | 'portrait';

@Component({
  selector: 'app-camera-modal',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="fixed inset-0 z-50 bg-black flex flex-col justify-between select-none overflow-hidden">
      <!-- Top Bar with Status, Controls and Close Button -->
      <div class="p-3 sm:p-4 flex items-center justify-between text-white bg-black/70 backdrop-blur-md z-30">
        <div class="flex items-center space-x-2">
          <span class="inline-block w-2.5 h-2.5 rounded-full bg-error animate-pulse"></span>
          <span class="font-bold text-xs sm:text-sm tracking-wide">Câmera Ativa</span>
          <span class="badge badge-xs badge-neutral text-[10px] hidden sm:inline-flex uppercase">
            {{ facingMode() === 'environment' ? 'Traseira' : 'Frontal' }}
          </span>
        </div>

        <div class="flex items-center space-x-2">
          <!-- Orientation toggle button in header -->
          <button
            type="button"
            (click)="toggleOrientation()"
            class="btn btn-xs sm:btn-sm btn-ghost gap-1 text-white border border-white/20 rounded-lg hover:bg-white/10"
            title="Alternar Orientação do Documento (Vertical / Horizontal)"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            <span class="text-[11px] font-medium">
              {{ orientation() === 'portrait' ? 'Vertical (Padrão)' : 'Horizontal' }}
            </span>
          </button>

          <!-- Close Modal Button -->
          <button
            type="button"
            (click)="close()"
            class="btn btn-circle btn-ghost btn-sm text-white hover:bg-white/10"
            title="Fechar Câmera"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>

      <!-- Live Video Viewport with Interactive Reticle Overlay -->
      <div class="relative flex-1 flex items-center justify-center overflow-hidden bg-black">
        <!-- Live Video Element (Optimized for iOS Safari and Android) -->
        <video
          #videoElement
          autoplay
          playsinline
          webkit-playsinline
          muted
          class="absolute inset-0 w-full h-full object-cover"
        ></video>

        <!-- Loading Spinner -->
        @if (isLoading()) {
          <div class="absolute inset-0 z-20 flex flex-col items-center justify-center bg-black/80 text-white space-y-3">
            <span class="loading loading-spinner loading-lg text-primary"></span>
            <p class="text-xs text-white/80 font-medium">Iniciando câmera traseira...</p>
          </div>
        }

        <!-- Permission / Device Error Banner -->
        @if (errorMessage()) {
          <div class="absolute inset-0 z-25 flex items-center justify-center p-4 bg-black/90">
            <div class="card bg-base-100 max-w-sm w-full p-5 text-center shadow-2xl border border-error/40 space-y-4">
              <div class="w-12 h-12 rounded-full bg-error/10 text-error flex items-center justify-center mx-auto">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              </div>
              <div>
                <h3 class="text-sm font-bold text-base-content">Acesso à Câmera</h3>
                <p class="text-xs text-base-content/70 mt-1.5 leading-relaxed">
                  {{ errorMessage() }}
                </p>
              </div>

              <!-- Native Smartphone Direct Camera Action -->
              <div class="space-y-2">
                <button
                  type="button"
                  (click)="openNativeCamera()"
                  class="btn btn-primary btn-sm w-full gap-2 shadow-md"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                  Tirar Foto com Câmera do Celular
                </button>
              </div>

              <div class="text-[11px] bg-base-200/80 p-2.5 rounded-lg text-left text-base-content/70 space-y-1">
                <p class="font-bold text-base-content">Para câmera ao vivo no navegador:</p>
                <p>• <strong>Android / Chrome:</strong> Permita nas permissões do site ou utilize HTTPS.</p>
                <p>• <strong>iOS / Safari:</strong> Acesse Ajustes > Safari > Câmera > Permitir.</p>
              </div>

              <div class="flex gap-2">
                <button type="button" (click)="startCamera()" class="btn btn-outline btn-sm flex-1">
                  Tentar Novamente
                </button>
                <button type="button" (click)="close()" class="btn btn-ghost btn-sm">
                  Cancelar
                </button>
              </div>
            </div>
          </div>
        }

        <!-- Reticle / Viewfinder Overlay (Helper Container with Smooth Rotation) -->
        <div
          class="relative z-10 transition-all duration-300 ease-out flex flex-col justify-between p-3.5 pointer-events-none rounded-2xl border-2 border-dashed border-white/80 shadow-[0_0_0_9999px_rgba(0,0,0,0.55)]"
          [ngClass]="{
            'h-[64vh] max-h-[500px] aspect-[1/1.58] w-auto max-w-[85vw]': orientation() === 'portrait',
            'w-[88vw] max-w-md aspect-[1.58/1] max-h-[60vh]': orientation() === 'landscape'
          }"
        >
          <!-- 4 Corner Brackets (Cantoneiras de Enquadramento Reforçadas) -->
          <div class="absolute -top-1.5 -left-1.5 w-7 h-7 border-t-4 border-l-4 border-primary rounded-tl-xl shadow-sm"></div>
          <div class="absolute -top-1.5 -right-1.5 w-7 h-7 border-t-4 border-r-4 border-primary rounded-tr-xl shadow-sm"></div>
          <div class="absolute -bottom-1.5 -left-1.5 w-7 h-7 border-b-4 border-l-4 border-primary rounded-bl-xl shadow-sm"></div>
          <div class="absolute -bottom-1.5 -right-1.5 w-7 h-7 border-b-4 border-r-4 border-primary rounded-br-xl shadow-sm"></div>

          <!-- Top Helper Message inside container -->
          <div class="bg-black/70 backdrop-blur-xs text-white text-[11px] sm:text-xs font-semibold text-center py-1.5 px-3 rounded-full mx-auto shadow-md border border-white/10">
            Posicione o documento dentro do retângulo
          </div>

          <!-- Bottom Helper Message inside container -->
          <div class="bg-black/70 backdrop-blur-xs text-white/90 text-[10px] sm:text-[11px] font-medium text-center py-1 px-3 rounded-full mx-auto shadow-md border border-white/10">
            Evite sombras, reflexos e fundos escuros
          </div>
        </div>

        <!-- Hidden Canvas for high-resolution frame snapshot -->
        <canvas #canvasElement class="hidden"></canvas>

        <!-- Hidden Native Camera File Input Fallback -->
        <input
          #nativeCameraInput
          type="file"
          accept="image/*"
          capture="environment"
          (change)="onNativeFileCaptured($event)"
          class="hidden"
        />
      </div>

      <!-- Bottom Control Bar -->
      <div class="p-4 sm:p-6 bg-black/80 backdrop-blur-md flex items-center justify-around z-30">
        <!-- Switch Camera (Front / Rear) -->
        <button
          type="button"
          (click)="toggleCameraFacing()"
          class="btn btn-circle btn-ghost text-white hover:bg-white/10"
          title="Alternar Câmera (Frontal / Traseira)"
          aria-label="Alternar Câmera"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        </button>

        <!-- Shutter Button (Disparo de Foto em Alta Resolução) -->
        <button
          type="button"
          (click)="captureFrame()"
          [disabled]="isLoading() || !!errorMessage()"
          class="w-18 h-18 sm:w-20 sm:h-20 rounded-full border-4 border-white bg-white/20 flex items-center justify-center active:scale-90 transition-transform shadow-2xl disabled:opacity-50"
          aria-label="Tirar foto"
          title="Capturar Documento"
        >
          <div class="w-13 h-13 sm:w-15 sm:h-15 rounded-full bg-white shadow-lg"></div>
        </button>

        <!-- Rotate Reticle Helper (Portrait / Landscape) -->
        <button
          type="button"
          (click)="toggleOrientation()"
          class="btn btn-circle btn-ghost text-white hover:bg-white/10"
          title="Girar Orientação do Enquadramento (Vertical / Horizontal)"
          aria-label="Girar Orientação"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
        </button>
      </div>
    </div>
  `,
})
export class CameraModalComponent implements OnInit, OnDestroy {
  @ViewChild('videoElement') videoRef!: ElementRef<HTMLVideoElement>;
  @ViewChild('canvasElement') canvasRef!: ElementRef<HTMLCanvasElement>;
  @ViewChild('nativeCameraInput') nativeCameraInputRef!: ElementRef<HTMLInputElement>;

  @Output() captured = new EventEmitter<File>();
  @Output() closed = new EventEmitter<void>();

  private mediaStream: MediaStream | null = null;
  public facingMode = signal<CameraFacing>('environment'); // Câmera traseira por padrão
  public orientation = signal<OverlayOrientation>('portrait'); // Vertical (Portrait) por padrão
  public isLoading = signal<boolean>(true);
  public errorMessage = signal<string | null>(null);

  public ngOnInit(): void {
    this.startCamera();
  }

  public ngOnDestroy(): void {
    this.stopCamera();
  }

  public async startCamera(): Promise<void> {
    this.isLoading.set(true);
    this.errorMessage.set(null);
    this.stopCamera();

    // Check if running in a secure context (HTTPS / localhost)
    const isSecure =
      typeof window !== 'undefined' &&
      (window.isSecureContext ||
        window.location.hostname === 'localhost' ||
        window.location.hostname === '127.0.0.1');

    if (
      typeof navigator === 'undefined' ||
      !navigator.mediaDevices ||
      !navigator.mediaDevices.getUserMedia ||
      !isSecure
    ) {
      this.errorMessage.set(
        'O navegador bloqueou a câmera ao vivo por estar em conexão HTTP na rede. Você pode tirar a foto diretamente pelo botão da câmera do celular abaixo.'
      );
      this.isLoading.set(false);
      return;
    }

    const requestedFacing = this.facingMode();

    // Try multiple constraints in order of preference
    const constraintsList: MediaStreamConstraints[] = [
      {
        video: {
          facingMode: { ideal: requestedFacing },
          width: { ideal: 1920 },
          height: { ideal: 1080 },
        },
        audio: false,
      },
      {
        video: {
          facingMode: requestedFacing,
        },
        audio: false,
      },
      {
        video: true,
        audio: false,
      },
    ];

    let stream: MediaStream | null = null;
    let lastError: any = null;

    for (const constraints of constraintsList) {
      try {
        stream = await navigator.mediaDevices.getUserMedia(constraints);
        if (stream) break;
      } catch (err: any) {
        lastError = err;
        if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
          break;
        }
      }
    }

    if (!stream) {
      this.isLoading.set(false);
      if (lastError?.name === 'NotAllowedError' || lastError?.name === 'PermissionDeniedError') {
        this.errorMessage.set(
          'O acesso à câmera ao vivo foi negado no navegador. Permita o acesso ou utilize o botão de câmera nativa do celular abaixo.'
        );
      } else if (lastError?.name === 'NotFoundError' || lastError?.name === 'DevicesNotFoundError') {
        this.errorMessage.set(
          'Nenhuma câmera foi encontrada no dispositivo. Utilize o botão da câmera nativa do celular.'
        );
      } else if (lastError?.name === 'NotReadableError' || lastError?.name === 'TrackStartError') {
        this.errorMessage.set(
          'A câmera está sendo utilizada por outro aplicativo. Feche outras abas ou utilize o botão de captura direta abaixo.'
        );
      } else {
        this.errorMessage.set(
          'Não foi possível inicializar a câmera ao vivo no navegador. Utilize o botão de câmera nativa do celular abaixo.'
        );
      }
      return;
    }

    this.mediaStream = stream;

    // Connect to video element with iOS Safari compatibility
    setTimeout(() => {
      if (this.videoRef && this.videoRef.nativeElement) {
        const video = this.videoRef.nativeElement;
        video.srcObject = stream;
        video.setAttribute('playsinline', 'true');
        video.setAttribute('webkit-playsinline', 'true');
        video.muted = true;

        video.onloadedmetadata = () => {
          video
            .play()
            .then(() => {
              this.isLoading.set(false);
            })
            .catch(() => {
              this.isLoading.set(false);
            });
        };
      } else {
        this.isLoading.set(false);
      }
    }, 50);
  }

  public toggleCameraFacing(): void {
    const nextMode: CameraFacing = this.facingMode() === 'environment' ? 'user' : 'environment';
    this.facingMode.set(nextMode);
    this.startCamera();
  }

  public toggleOrientation(): void {
    const nextOrientation: OverlayOrientation =
      this.orientation() === 'portrait' ? 'landscape' : 'portrait';
    this.orientation.set(nextOrientation);
  }

  public captureFrame(): void {
    if (!this.videoRef || !this.videoRef.nativeElement || !this.canvasRef || !this.canvasRef.nativeElement) {
      return;
    }

    const video = this.videoRef.nativeElement;
    const canvas = this.canvasRef.nativeElement;

    const width = video.videoWidth || 1920;
    const height = video.videoHeight || 1080;

    canvas.width = width;
    canvas.height = height;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    if (this.facingMode() === 'user') {
      ctx.translate(width, 0);
      ctx.scale(-1, 1);
    }

    ctx.drawImage(video, 0, 0, width, height);

    canvas.toBlob(
      (blob) => {
        if (blob) {
          const timestamp = Date.now();
          const file = new File([blob], `documento_captura_${timestamp}.jpg`, {
            type: 'image/jpeg',
          });
          this.captured.emit(file);
          this.close();
        }
      },
      'image/jpeg',
      0.95
    );
  }

  public openNativeCamera(): void {
    if (this.nativeCameraInputRef && this.nativeCameraInputRef.nativeElement) {
      this.nativeCameraInputRef.nativeElement.click();
    }
  }

  public onNativeFileCaptured(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files[0]) {
      const file = input.files[0];
      this.captured.emit(file);
      this.close();
    }
  }

  public stopCamera(): void {
    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach((track) => {
        try {
          track.stop();
        } catch {
          // ignore cleanup errors
        }
      });
      this.mediaStream = null;
    }
  }

  public close(): void {
    this.stopCamera();
    this.closed.emit();
  }
}
