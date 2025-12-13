import { createWorker, Worker, PSM } from 'tesseract.js';

class OCRService {
    private worker: Worker | null = null;
    private workerPromise: Promise<Worker> | null = null;

    private async getWorker(): Promise<Worker> {
        if (this.worker) return this.worker;

        if (!this.workerPromise) {
            this.workerPromise = (async () => {
                try {
                    // Initialize with default OEM
                    const worker = await createWorker('eng', undefined);

                    // Set Page Segmentation Mode to AUTO to ensure we get blocks/words
                    await worker.setParameters({
                        tessedit_pageseg_mode: PSM.AUTO,
                    });

                    this.worker = worker;
                    return worker;
                } catch (error) {
                    console.error('Failed to initialize Tesseract worker:', error);
                    this.workerPromise = null;
                    throw error;
                }
            })();
        }

        return this.workerPromise;
    }

    async recognize(imagePath: string) {
        try {
            const worker = await this.getWorker();
            const result = await worker.recognize(imagePath);
            return result.data;
        } catch (error) {
            console.error('OCR Error:', error);
            throw error;
        }
    }

    async terminate() {
        if (this.workerPromise) {
            try {
                const worker = await this.workerPromise;
                await worker.terminate();
            } catch {
                // Initialization failed, nothing to terminate
            }
        }
        this.worker = null;
        this.workerPromise = null;
    }
}

export const ocrService = new OCRService();
