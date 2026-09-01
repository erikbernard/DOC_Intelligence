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

@Component({
  selector: 'app-camera-modal',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="fixed inset-0 z-50 bg-black flex flex-col justify-between">
      <!-- Top Bar with Hints and Close -->
      <div class="p-4 flex items-center justify-between text-white bg-black/60 backdrop-blur-xs z-20">
        <div class="flex items-center space-x-2">
          <span class="inline-block w-2.5 h-2.5 rounded-full bg-error animate-pulse"></span>
          <span class="font-bold text-sm">Câmera Ativa</span>
        </div>
        <button (click)="close()" class="btn btn-circle btn-ghost btn-sm text-white">
          ✕
        </button>
      </div>

      <!-- Live Video Viewport with Interactive Reticle Overlay -->
      <div class="relative flex-1 flex items-center justify-center overflow-hidden bg-black">
        <video
          #videoElement
          autoplay
          playsinline
          muted
          class="absolute inset-0 w-full h-full object-cover"
        ></video>

        <!-- Reticle / Viewfinder Overlay -->
        <div class="relative z-10 w-[88vw] max-w-sm aspect-[1.58/1] rounded-xl border-2 border-dashed border-white/80 shadow-2xl flex flex-col justify-between p-3 pointer-events-none">
          <!-- 4 Corner Brackets (Cantoneiras de Enquadramento) -->
          <div class="absolute -top-1 -left-1 w-6 h-6 border-t-4 border-l-4 border-primary rounded-tl-lg"></div>
          <div class="absolute -top-1 -right-1 w-6 h-6 border-t-4 border-r-4 border-primary rounded-tr-lg"></div>
          <div class="absolute -bottom-1 -left-1 w-6 h-6 border-b-4 border-l-4 border-primary rounded-bl-lg"></div>
          <div class="absolute -bottom-1 -right-1 w-6 h-6 border-b-4 border-r-4 border-primary rounded-br-lg"></div>

          <!-- Alignment instruction message -->
          <div class="bg-black/60 backdrop-blur-xs text-white text-[11px] font-medium text-center py-1 px-2 rounded-md mx-auto">
            Posicione o documento dentro do retângulo
          </div>

          <div class="bg-black/60 backdrop-blur-xs text-white/80 text-[10px] text-center py-0.5 px-2 rounded-md mx-auto">
            Evite sombras e reflexos de luz
          </div>
        </div>

        <!-- Hidden Canvas for frame snapshot -->
        <canvas #canvasElement class="hidden"></canvas>
      </div>

      <!-- Bottom Control Bar -->
      <div class="p-6 bg-black/80 backdrop-blur-xs flex items-center justify-around z-20">
        <!-- Switch Camera (Front / Rear) -->
        <button (click)="toggleCameraFacing()" class="btn btn-circle btn-ghost text-white" title="Alternar Câmera">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        </button>

        <!-- Shutter Button (Disparo) -->
        <button
          (click)="captureFrame()"
          class="w-18 h-18 rounded-full border-4 border-white bg-white/20 flex items-center justify-center active:scale-95 transition-transform"
          aria-label="Tirar foto"
        >
          <div class="w-13 h-13 rounded-full bg-white shadow-lg"></div>
        </button>

        <!-- Cancel button -->
        <button (click)="close()" class="btn btn-circle btn-ghost text-white" title="Cancelar">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </div>
  `,
})
export class CameraModalComponent implements OnInit, OnDestroy {
  @ViewChild('videoElement') videoRef!: ElementRef<HTMLVideoElement>;
  @ViewChild('canvasElement') canvasRef!: ElementRef<HTMLCanvasElement>;

  @Output() captured = new EventEmitter<File>();
  @Output() closed = new EventEmitter<void>();

  private mediaStream: MediaStream | null = null;
  private currentFacingMode: 'environment' | 'user' = 'environment';
  public error = signal<string | null>(null);

  public ngOnInit(): void {
    this.startCamera();
  }

  public ngOnDestroy(): void {
    this.stopCamera();
  }

  public async startCamera(): Promise<void> {
    this.stopCamera();
    try {
      const constraints: MediaStreamConstraints = {
        video: {
          facingMode: { ideal: this.currentFacingMode },
          width: { ideal: 1920 },
          height: { ideal: 1080 },
        },
        audio: false,
      };

      this.mediaStream = await navigator.mediaDevices.getUserMedia(constraints);
      if (this.videoRef && this.videoRef.nativeElement) {
        this.videoRef.nativeElement.srcObject = this.mediaStream;
      }
    } catch (err: any) {
      this.error.set(
        'Não foi possível acessar a câmera do dispositivo. Verifique as permissões no navegador.'
      );
    }
  }

  public toggleCameraFacing(): void {
    this.currentFacingMode = this.currentFacingMode === 'environment' ? 'user' : 'environment';
    this.startCamera();
  }

  public captureFrame(): void {
    const video = this.videoRef.nativeElement;
    const canvas = this.canvasRef.nativeElement;

    if (!video || !canvas) return;

    canvas.width = video.videoWidth || 1280;
    canvas.height = video.videoHeight || 720;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    canvas.toBlob(
      (blob) => {
        if (blob) {
          const timestamp = new Date().getTime();
          const file = new File([blob], `documento_captura_${timestamp}.jpg`, {
            type: 'image/jpeg',
          });
          this.captured.emit(file);
          this.stopCamera();
        }
      },
      'image/jpeg',
      0.95
    );
  }

  public stopCamera(): void {
    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach((track) => track.stop());
      this.mediaStream = null;
    }
  }

  public close(): void {
    this.stopCamera();
    this.closed.emit();
  }
}
