// Envía el token JWT del login (guardado por js/auth.js)
function fetchConToken(url, opciones = {}) {
    const token = localStorage.getItem("token") || sessionStorage.getItem("token");
    if (!token) {
        window.location.href = "../login.html";
        throw new Error("Sin sesión iniciada");
    }
    return fetch(url, {
        ...opciones,
        headers: { ...(opciones.headers || {}), Authorization: "Bearer " + token }
    });
}

const API_URL = "http://127.0.0.1:8000/api/attendance/camera/check-in";
const RESET_URL = "http://127.0.0.1:8000/api/attendance/camera/reset";


class AttendanceCamera {

    constructor(videoElement, callbacks = {}) {

        this.video = videoElement;

        this.onStatus = callbacks.onStatus || (() => {});
        this.onSuccess = callbacks.onSuccess || (() => {});
        this.onAlreadyRegistered =
            callbacks.onAlreadyRegistered || (() => {});
        this.onError = callbacks.onError || (() => {});

        this.stream = null;
        this.running = false;
        this.processing = false;

        this.interval = 1000;
        this.timer = null;
    }


    async start() {

        try {

            await this.resetBackend();

            if (!this.stream) {

                this.stream =
                    await navigator.mediaDevices.getUserMedia({
                        video: {
                            width: { ideal: 640 },
                            height: { ideal: 480 },
                            facingMode: "user"
                        },
                        audio: false
                    });

                this.video.srcObject = this.stream;

                await this.video.play();
            }

            this.running = true;
            this.processing = false;

            this.onStatus({
                status: "WAITING",
                message: "Acércate a la cámara"
            });

            this.processLoop();

        } catch (error) {

            console.error(error);

            this.onError(
                "No se pudo acceder a la cámara"
            );
        }
    }


    async resetBackend() {

        try {

            await fetchConToken(RESET_URL, {
                method: "POST"
            });

        } catch (error) {

            console.warn(
                "No se pudo reiniciar la sesión:",
                error
            );
        }
    }


    async processLoop() {

        if (!this.running) {
            return;
        }

        if (!this.processing) {
            await this.processFrame();
        }

        if (this.running) {

            this.timer = setTimeout(
                () => this.processLoop(),
                this.interval
            );
        }
    }


    async processFrame() {

        if (
            !this.video.videoWidth ||
            !this.video.videoHeight
        ) {
            return;
        }

        this.processing = true;

        try {

            const canvas =
                document.createElement("canvas");

            canvas.width =
                this.video.videoWidth;

            canvas.height =
                this.video.videoHeight;

            const context =
                canvas.getContext("2d");

            context.drawImage(
                this.video,
                0,
                0,
                canvas.width,
                canvas.height
            );

            const image =
                canvas
                    .toDataURL("image/jpeg", 0.75)
                    .split(",")[1];

            const response =
                await fetchConToken(
                    API_URL,
                    {
                        method: "POST",
                        headers: {
                            "Content-Type":
                                "application/json"
                        },
                        body: JSON.stringify({
                            image: image
                        })
                    }
                );

            const data =
                await response.json();

            this.handleResponse(data);

        } catch (error) {

            console.error(
                "Error procesando cámara:",
                error
            );

        } finally {

            this.processing = false;
        }
    }


    handleResponse(data) {

        const status = data.status;


        if (status === "NO_FACE") {

            this.onStatus({
                status: "WAITING",
                message: "Acércate a la cámara"
            });

            return;
        }


        if (status === "MULTIPLE_FACES") {

            this.onStatus({
                status: "ERROR",
                message: "Debe haber un solo rostro"
            });

            return;
        }


        if (status === "UNKNOWN_FACE") {

            this.onStatus({
                status: "ERROR",
                message: "Rostro no reconocido"
            });

            return;
        }


        if (status === "INVALID_FACE") {

            this.onStatus({
                status: "ERROR",
                message: "No se pudo detectar el rostro"
            });

            return;
        }


        if (status === "LIVENESS_PENDING") {

            this.onStatus({
                status: "VERIFYING",
                message: "Verificando identidad..."
            });

            return;
        }


        if (status === "RECOGNITION_PENDING") {

            this.onStatus({
                status: "VERIFYING",
                message: "Confirmando identidad..."
            });

            return;
        }


        if (status === "REGISTERED") {

            this.pause();

            this.onSuccess(data);

            return;
        }


        if (status === "ALREADY_REGISTERED") {

            this.pause();

            this.onAlreadyRegistered(data);

            return;
        }


        this.onStatus({
            status: "WAITING",
            message: "Acércate a la cámara"
        });
    }


    pause() {

        this.running = false;

        if (this.timer) {

            clearTimeout(this.timer);

            this.timer = null;
        }

        this.processing = false;
    }


    async restart() {

        this.pause();

        await this.resetBackend();

        this.running = true;
        this.processing = false;

        this.onStatus({
            status: "WAITING",
            message: "Acércate a la cámara"
        });

        this.processLoop();
    }


    stop() {

        this.pause();

        if (this.stream) {

            this.stream
                .getTracks()
                .forEach(track => track.stop());

            this.stream = null;
        }

        this.video.srcObject = null;
    }
}


window.AttendanceCamera = AttendanceCamera;
