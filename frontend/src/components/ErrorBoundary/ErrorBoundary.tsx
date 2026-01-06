import { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RotateCw } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface ErrorBoundaryProps {
  children: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  isRetrying: boolean;
}

/**
 * ErrorBoundary catches JavaScript errors anywhere in the child component tree,
 * logs those errors, and displays a fallback UI instead of crashing the app.
 */
class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null, isRetrying: false };
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return { hasError: true, error, isRetrying: false };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    console.error('ErrorBoundary caught an error:', error);
    console.error('Component stack:', errorInfo.componentStack);
  }

  handleRetry = (): void => {
    this.setState({ isRetrying: true }, () => {
      // Small delay to show the spinner, then attempt recovery
      setTimeout(() => {
        this.setState({ hasError: false, error: null, isRetrying: false });
      }, 500);
    });
  };

  render(): ReactNode {
    if (this.state.hasError) {
      return (
        <div className="bg-background flex min-h-screen flex-col items-center justify-center p-6">
          <div className="bg-card w-full max-w-md rounded-lg border p-8 text-center shadow-lg">
            <div className="bg-destructive/10 mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-full">
              <AlertTriangle className="text-destructive h-8 w-8" />
            </div>

            <h1 className="text-foreground mb-2 text-2xl font-bold">
              Something went wrong
            </h1>

            <p className="text-muted-foreground mb-6">
              An unexpected error occurred. Please try reloading the
              application.
            </p>

            <Button onClick={this.handleRetry} disabled={this.state.isRetrying}>
              <RotateCw
                className={`mr-2 h-4 w-4 ${this.state.isRetrying ? 'animate-spin' : ''}`}
              />
              {this.state.isRetrying ? 'Reloading...' : 'Reload App'}
            </Button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
