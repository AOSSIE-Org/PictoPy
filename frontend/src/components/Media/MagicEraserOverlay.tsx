import React, { useRef, useState, useEffect } from 'react';
import { Eraser, Undo, Redo, X, Check, Loader2 } from 'lucide-react';
import { convertFileSrc } from '@tauri-apps/api/core';

interface MagicEraserOverlayProps {
    imagePath: string;
    onClose: () => void;
    onSave: (newImagePath: string) => void;
    originalWidth: number;
    originalHeight: number;
}

export const MagicEraserOverlay: React.FC<MagicEraserOverlayProps> = ({
    imagePath,
    onClose,
    onSave,
    originalWidth,
    originalHeight,
}) => {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const containerRef = useRef<HTMLDivElement>(null);
    const [isDrawing, setIsDrawing] = useState(false);
    const [brushSize, setBrushSize] = useState(20);
    const [isProcessing, setIsProcessing] = useState(false);
    const [previewImage, setPreviewImage] = useState<string | null>(null);

    // History for undo/redo (store canvas data URLs or ImageData)
    // For simplicity, we just clear for now, but undo is requested in plan.
    // We'll implement basic path history.
    const [paths, setPaths] = useState<{ x: number; y: number; size: number }[][]>([]);
    const [poppedPaths, setPoppedPaths] = useState<{ x: number; y: number; size: number }[][]>([]);
    const [currentPath, setCurrentPath] = useState<{ x: number; y: number; size: number }[]>([]);

    // Setup canvas size
    useEffect(() => {
        const canvas = canvasRef.current;
        const container = containerRef.current;
        if (canvas && container) {
            canvas.width = container.clientWidth;
            canvas.height = container.clientHeight;

            const ctx = canvas.getContext('2d');
            if (ctx) {
                ctx.lineCap = 'round';
                ctx.lineJoin = 'round';
                ctx.strokeStyle = 'rgba(255, 0, 0, 0.5)'; // Visual red mask
            }
        }
    }, []);

    // Redraw when paths change (Undo/Redo logic would go here)
    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Draw all committed paths
        ctx.strokeStyle = 'rgba(255, 0, 0, 0.5)';
        paths.forEach(path => {
            if (path.length < 1) return;
            ctx.beginPath();
            ctx.lineWidth = path[0].size;
            ctx.moveTo(path[0].x, path[0].y);
            for (let i = 1; i < path.length; i++) {
                ctx.lineTo(path[i].x, path[i].y);
            }
            ctx.stroke();
        });

        // Draw current path
        if (currentPath.length > 0) {
            ctx.beginPath();
            ctx.lineWidth = currentPath[0].size;
            ctx.moveTo(currentPath[0].x, currentPath[0].y);
            for (let i = 1; i < currentPath.length; i++) {
                ctx.lineTo(currentPath[i].x, currentPath[i].y);
            }
            ctx.stroke();
        }
    }, [paths, currentPath]);

    const getPointerPos = (e: React.MouseEvent | React.TouchEvent) => {
        const canvas = canvasRef.current;
        if (!canvas) return { x: 0, y: 0 };
        const rect = canvas.getBoundingClientRect();
        let clientX, clientY;

        if ('touches' in e) {
            clientX = e.touches[0].clientX;
            clientY = e.touches[0].clientY;
        } else {
            clientX = (e as React.MouseEvent).clientX;
            clientY = (e as React.MouseEvent).clientY;
        }

        return {
            x: clientX - rect.left,
            y: clientY - rect.top
        };
    };

    const startDrawing = (e: React.MouseEvent | React.TouchEvent) => {
        setIsDrawing(true);
        const pos = getPointerPos(e);
        setCurrentPath([{ x: pos.x, y: pos.y, size: brushSize }]);
    };

    const draw = (e: React.MouseEvent | React.TouchEvent) => {
        if (!isDrawing) return;
        const pos = getPointerPos(e);
        setCurrentPath(prev => [...prev, { x: pos.x, y: pos.y, size: brushSize }]);
    };

    const stopDrawing = () => {
        if (!isDrawing) return;
        setIsDrawing(false);
        if (currentPath.length > 0) {
            setPaths(prev => [...prev, currentPath]);
            setCurrentPath([]);
            setPoppedPaths([]); // Clear redo history
        }
    };

    const [error, setError] = useState<string | null>(null);

    const handleErase = async () => {
        if (paths.length === 0) return;

        setIsProcessing(true);
        setError(null);
        try {
            // 1. Generate Mask Data URL
            // We need a separate canvas for the actual mask (white on black)
            const maskCanvas = document.createElement('canvas');
            maskCanvas.width = originalWidth;
            maskCanvas.height = originalHeight;
            const ctx = maskCanvas.getContext('2d');
            if (!ctx || !canvasRef.current) return;

            ctx.fillStyle = 'black';
            ctx.fillRect(0, 0, maskCanvas.width, maskCanvas.height);

            // Scale factor between display canvas and original image
            const scaleX = originalWidth / canvasRef.current.width;
            const scaleY = originalHeight / canvasRef.current.height;

            ctx.strokeStyle = 'white';
            ctx.lineCap = 'round';
            ctx.lineJoin = 'round';

            paths.forEach(path => {
                if (path.length < 1) return;
                ctx.beginPath();
                ctx.lineWidth = path[0].size * ((scaleX + scaleY) / 2); // Approximation
                ctx.moveTo(path[0].x * scaleX, path[0].y * scaleY);
                for (let i = 1; i < path.length; i++) {
                    ctx.lineTo(path[i].x * scaleX, path[i].y * scaleY);
                }
                ctx.stroke();
            });

            const maskData = maskCanvas.toDataURL('image/png');

            // 2. Call API
            const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
            const response = await fetch(`${apiUrl}/edit/magic-eraser`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    image_path: imagePath,
                    mask_data: maskData,
                }),
            });

            const data = await response.json();
            if (data.success) {
                setPreviewImage(data.image_data);
            } else {
                console.error('Magic Eraser failed:', data.error);
                setError(data.error || 'Failed to process image');
            }

        } catch (error) {
            console.error('Error:', error);
            setError('Network error. Please try again.');
        } finally {
            setIsProcessing(false);
        }
    };

    const handleUndo = () => {
        if (paths.length === 0) return;
        const lastPath = paths[paths.length - 1];
        setPaths(prev => prev.slice(0, -1));
        setPoppedPaths(prev => [...prev, lastPath]);
    };

    const handleRedo = () => {
        if (poppedPaths.length === 0) return;
        const pathRestored = poppedPaths[poppedPaths.length - 1];
        setPoppedPaths(prev => prev.slice(0, -1));
        setPaths(prev => [...prev, pathRestored]);
    };

    const handleScaleBrush = (e: React.ChangeEvent<HTMLInputElement>) => {
        setBrushSize(parseInt(e.target.value));
    };

    return (
        <div className="absolute inset-0 z-50 flex flex-col bg-black/80 backdrop-blur-sm animate-in fade-in duration-300">
            {/* Top Bar */}
            <div className="flex items-center justify-between px-6 py-4 bg-black/40 border-b border-white/10">
                <h3 className="text-white font-medium flex items-center gap-2">
                    <Eraser className="w-5 h-5 text-purple-400" />
                    Magic Eraser
                </h3>
                <button onClick={onClose} className="p-2 hover:bg-white/10 rounded-full text-white/70 hover:text-white transition-colors">
                    <X className="w-5 h-5" />
                </button>
            </div>

            {/* Main Area */}
            <div className="flex-1 relative overflow-hidden flex items-center justify-center p-8">
                <div ref={containerRef} className="relative shadow-2xl rounded-lg overflow-hidden border border-white/10" style={{ maxWidth: '100%', maxHeight: '100%', aspectRatio: `${originalWidth}/${originalHeight}` }}>
                    {/* Base Image */}
                    <img
                        src={previewImage || convertFileSrc(imagePath)}
                        alt="Editing"
                        className="w-full h-full object-contain pointer-events-none select-none"
                    />

                    {/* Drawing Canvas */}
                    {!previewImage && (
                        <canvas
                            ref={canvasRef}
                            className="absolute inset-0 cursor-crosshair touch-none"
                            onMouseDown={startDrawing}
                            onMouseMove={draw}
                            onMouseUp={stopDrawing}
                            onMouseLeave={stopDrawing}
                            onTouchStart={startDrawing}
                            onTouchMove={draw}
                            onTouchEnd={stopDrawing}
                        />
                    )}

                    {/* Loading Overlay */}
                    {isProcessing && (
                        <div className="absolute inset-0 bg-black/60 flex flex-col items-center justify-center backdrop-blur-sm z-10">
                            <Loader2 className="w-10 h-10 text-purple-500 animate-spin mb-3" />
                            <span className="text-white font-medium">Removing Object...</span>
                        </div>
                    )}

                    {/* Error Overlay */}
                    {error && (
                        <div className="absolute inset-0 z-20 flex items-center justify-center pointer-events-none">
                            <div className="bg-red-500/90 text-white px-6 py-3 rounded-xl shadow-2xl backdrop-blur-md border border-white/20">
                                <p className="font-medium text-center">{error}</p>
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {/* Bottom Controls */}
            <div className="px-6 py-6 bg-black/80 border-t border-white/10 flex items-center justify-center gap-6">
                {!previewImage ? (
                    <>
                        <div className="flex items-center gap-4 bg-zinc-900/80 px-4 py-2 rounded-full border border-white/10">
                            <span className="text-xs text-white/50 font-medium uppercase tracking-wider">Brush Size</span>
                            <input
                                type="range"
                                min="5"
                                max="100"
                                value={brushSize}
                                onChange={handleScaleBrush}
                                className="w-32 h-1.5 bg-white/20 rounded-lg appearance-none cursor-pointer hover:bg-white/30 transition-colors [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-3.5 [&::-webkit-slider-thumb]:h-3.5 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-purple-500"
                            />
                            <div className="w-8 text-right text-sm text-white/80">{brushSize}px</div>
                        </div>

                        <div className="h-8 w-[1px] bg-white/10 mx-2" />

                        <button
                            onClick={handleUndo}
                            disabled={paths.length === 0}
                            className="p-3 rounded-full bg-zinc-900/80 text-white/90 hover:bg-white/10 hover:text-white disabled:opacity-50 disabled:hover:bg-zinc-900/80 transition-all border border-white/10"
                            title="Undo"
                        >
                            <Undo className="w-5 h-5" />
                        </button>

                        <button
                            onClick={handleRedo}
                            disabled={poppedPaths.length === 0}
                            className="p-3 rounded-full bg-zinc-900/80 text-white/90 hover:bg-white/10 hover:text-white disabled:opacity-50 disabled:hover:bg-zinc-900/80 transition-all border border-white/10"
                            title="Redo"
                        >
                            <Redo className="w-5 h-5" />
                        </button>

                        <button
                            onClick={handleErase}
                            disabled={paths.length === 0}
                            className="flex items-center gap-2 px-6 py-3 rounded-full bg-purple-600 text-white hover:bg-purple-500 hover:shadow-[0_0_20px_rgba(168,85,247,0.4)] disabled:opacity-50 disabled:cursor-not-allowed disabled:shadow-none transition-all font-medium"
                        >
                            <Eraser className="w-5 h-5" />
                            <span>Erase Object</span>
                        </button>
                    </>
                ) : (
                    <>
                        <button
                            onClick={() => {
                                setPreviewImage(null);
                                setPaths([]); // Clear paths or keep them? Usually clear if we want fresh edit.
                            }}
                            className="px-6 py-2.5 rounded-full bg-zinc-800 text-white hover:bg-zinc-700 transition-colors font-medium border border-white/10"
                        >
                            Discard
                        </button>
                        <button
                            onClick={() => onSave(previewImage!)}
                            className="flex items-center gap-2 px-6 py-2.5 rounded-full bg-green-600 text-white hover:bg-green-500 hover:shadow-lg transition-all font-medium"
                        >
                            <Check className="w-4 h-4" />
                            <span>Save Changes</span>
                        </button>
                    </>
                )}
            </div>
        </div>
    );
};
