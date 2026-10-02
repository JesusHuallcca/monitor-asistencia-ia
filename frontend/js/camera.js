const Camara = {
  stream: null,

  // Pide permiso al navegador y muestra la cámara en el <video>
  async iniciar(video) {
    if (
      !window.isSecureContext ||
      !navigator.mediaDevices ||
      !navigator.mediaDevices.getUserMedia
    ) {
      throw new Error(
        "Este navegador o dirección no permite usar la cámara. Abre la página desde http://127.0.0.1:5500.",
      );
    }
    try {
      this.stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 640 },
          height: { ideal: 480 },
          facingMode: "user",
        },
        audio: false,
      });
    } catch (e) {
      throw new Error(this._mensaje(e));
    }
    video.srcObject = this.stream;
    await video.play();
  },

  detener(video) {
    if (this.stream) {
      this.stream.getTracks().forEach((t) => t.stop());
      this.stream = null;
    }
    if (video) video.srcObject = null;
  },

  // Devuelve un fotograma como imagen JPEG en base64 (sin espejo)
  capturar(video, anchoMax = 640, calidad = 0.85) {
    if (!video.videoWidth) throw new Error("La cámara aún no está lista.");
    const escala = Math.min(1, anchoMax / video.videoWidth);
    const canvas = document.createElement("canvas");
    canvas.width = Math.round(video.videoWidth * escala);
    canvas.height = Math.round(video.videoHeight * escala);
    canvas.getContext("2d").drawImage(video, 0, 0, canvas.width, canvas.height);
    return canvas.toDataURL("image/jpeg", calidad);
  },

  _mensaje(e) {
    switch (e.name) {
      case "NotAllowedError":
      case "SecurityError":
        return "Permiso de cámara denegado. Pulsa el candado junto a la dirección, permite la cámara y vuelve a intentar.";
      case "NotFoundError":
      case "OverconstrainedError":
        return "No se encontró ninguna cámara.";
      case "NotReadableError":
        return "La cámara está siendo usada por otra aplicación.";
      default:
        return "No se pudo activar la cámara.";
    }
  },
};
