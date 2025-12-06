import React, { useEffect, useState } from 'react';
import { Page } from 'tesseract.js';
import { Check } from 'lucide-react';

interface TextOverlayProps {
    ocrData: Page | null;
    scale?: number;
}

export const TextOverlay: React.FC<TextOverlayProps> = ({ ocrData, scale = 1 }) => {
    const [showCopyFeedback, setShowCopyFeedback] = useState(false);

    useEffect(() => {
        let feedbackTimeout: ReturnType<typeof setTimeout>;

        const handleKeyDown = async (e: KeyboardEvent) => {
            if (e.ctrlKey && e.key.toLowerCase() === 'c') {
                const selection = window.getSelection();
                const text = selection?.toString().trim();

                if (text && text.length > 0) {
                    // We manually write to clipboard to ensure it works even with transparent text
                    try {
                        await navigator.clipboard.writeText(text);
                        setShowCopyFeedback(true);
                        feedbackTimeout = setTimeout(() => setShowCopyFeedback(false), 2000);
                    } catch (err) {
                        console.error('Failed to copy text:', err);
                    }
                }
            }
        };

        window.addEventListener('keydown', handleKeyDown);
        return () => {
            window.removeEventListener('keydown', handleKeyDown);
            clearTimeout(feedbackTimeout);
        };
    }, []);

    if (!ocrData) return null;

    // Use lines instead of words for better sentence selection
    const lines = (ocrData as any).lines || [];

    return (
        <>
            {showCopyFeedback && (
                <div
                    className="fixed bottom-8 left-1/2 transform -translate-x-1/2 z-100 bg-zinc-900/90 text-white px-4 py-2.5 rounded-full flex items-center gap-2.5 backdrop-blur-md shadow-xl border border-white/10 animate-in fade-in slide-in-from-bottom-4 duration-300"
                >
                    <div className="bg-green-500/20 p-1 rounded-full">
                        <Check className="w-3.5 h-3.5 text-green-400" />
                    </div>
                    <span className="text-sm font-medium tracking-wide">Text copied to clipboard</span>
                </div>
            )}

            <div
                className="ocr-overlay-container"
                onMouseDown={(e) => e.stopPropagation()}
                style={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    width: '100%',
                    height: '100%',
                    pointerEvents: 'auto',
                    zIndex: 60,
                    userSelect: 'text',
                    WebkitUserSelect: 'text',
                    opacity: 0,
                    animation: 'fadeIn 0.3s ease-out forwards',
                }}
            >
                {lines.map((line: any, index: number) => {
                    const { bbox, text } = line;
                    const width = (bbox.x1 - bbox.x0) * scale;
                    const height = (bbox.y1 - bbox.y0) * scale;
                    const left = bbox.x0 * scale;
                    const top = bbox.y0 * scale;

                    return (
                        <span
                            key={`${index}-${text}`}
                            className="ocr-line"
                            style={{
                                position: 'absolute',
                                left: `${left}px`,
                                top: `${top}px`,
                                width: `${width}px`,
                                height: `${height}px`,
                                fontSize: `${height * 0.85}px`,
                                lineHeight: 1,
                                color: 'transparent',
                                userSelect: 'text',
                                pointerEvents: 'auto',
                                cursor: 'text',
                                whiteSpace: 'nowrap',
                                overflow: 'hidden',
                                display: 'flex',
                                alignItems: 'center',
                            }}
                            title={text}
                        >
                            {text}
                        </span>
                    );
                })}
                <style>{`
            @keyframes fadeIn {
                from { opacity: 0; }
                to { opacity: 1; }
            }
            .ocr-line {
              background-color: rgba(168, 85, 247, 0.08);
              transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
              border-radius: 3px;
            }
            .ocr-line:hover {
              background-color: rgba(168, 85, 247, 0.25);
              box-shadow: 0 0 0 1px rgba(168, 85, 247, 0.4);
              transform: scale(1.01);
              z-index: 10;
            }
            .ocr-line::selection {
              background-color: rgba(168, 85, 247, 0.5);
              color: transparent;
            }
          `}</style>
            </div>
        </>
    );
};
