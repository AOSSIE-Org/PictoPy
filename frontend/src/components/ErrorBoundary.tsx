import { Component, ErrorInfo, ReactNode } from 'react';

interface ErrorBoundaryProps {
    children: ReactNode;
    fallback?: ReactNode;
}

interface ErrorBoundaryState {
    hasError: boolean;
    error: Error | null;
}

class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
    constructor(props: ErrorBoundaryProps) {
        super(props);
        this.state = { hasError: false, error: null };
    }

    static getDerivedStateFromError(error: Error): ErrorBoundaryState {
        return { hasError: true, error };
    }

    componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
        console.error('ErrorBoundary caught an error:', error, errorInfo);
    }

    handleReset = (): void => {
        this.setState({ hasError: false, error: null });
    };

    handleReload = (): void => {
        window.location.reload();
    };

    render(): ReactNode {
        if (this.state.hasError) {
            if (this.props.fallback) {
                return this.props.fallback;
            }

            return (
                <div
                    style={{
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        justifyContent: 'center',
                        height: '100vh',
                        padding: '2rem',
                        textAlign: 'center',
                        backgroundColor: '#0a0a0a',
                        color: '#e5e5e5',
                    }}
                >
                    <div
                        style={{
                            maxWidth: '480px',
                            padding: '2rem',
                            borderRadius: '12px',
                            backgroundColor: '#1a1a1a',
                            border: '1px solid #333',
                        }}
                    >
                        <h2
                            style={{
                                fontSize: '1.5rem',
                                fontWeight: 600,
                                marginBottom: '0.75rem',
                                color: '#f87171',
                            }}
                        >
                            Something went wrong
                        </h2>
                        <p
                            style={{
                                fontSize: '0.95rem',
                                color: '#a1a1aa',
                                marginBottom: '1.5rem',
                                lineHeight: 1.5,
                            }}
                        >
                            An unexpected error occurred. You can try again or reload the
                            application.
                        </p>
                        {this.state.error && (
                            <pre
                                style={{
                                    fontSize: '0.75rem',
                                    color: '#f87171',
                                    backgroundColor: '#2a1a1a',
                                    padding: '0.75rem',
                                    borderRadius: '8px',
                                    marginBottom: '1.5rem',
                                    overflow: 'auto',
                                    maxHeight: '120px',
                                    textAlign: 'left',
                                }}
                            >
                                {this.state.error.message}
                            </pre>
                        )}
                        <div
                            style={{ display: 'flex', gap: '0.75rem', justifyContent: 'center' }}
                        >
                            <button
                                onClick={this.handleReset}
                                style={{
                                    padding: '0.5rem 1.25rem',
                                    borderRadius: '8px',
                                    border: '1px solid #555',
                                    backgroundColor: 'transparent',
                                    color: '#e5e5e5',
                                    cursor: 'pointer',
                                    fontSize: '0.875rem',
                                }}
                            >
                                Try Again
                            </button>
                            <button
                                onClick={this.handleReload}
                                style={{
                                    padding: '0.5rem 1.25rem',
                                    borderRadius: '8px',
                                    border: 'none',
                                    backgroundColor: '#3b82f6',
                                    color: '#fff',
                                    cursor: 'pointer',
                                    fontSize: '0.875rem',
                                }}
                            >
                                Reload App
                            </button>
                        </div>
                    </div>
                </div>
            );
        }

        return this.props.children;
    }
}

export default ErrorBoundary;
