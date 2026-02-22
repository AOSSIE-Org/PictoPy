import { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RotateCw, ChevronDown, ChevronUp } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface ErrorBoundaryProps {
  children: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  isRetrying: boolean;
  showDetails: boolean;
}

/**
 * ErrorBoundary catches JavaScript errors anywhere in the child component tree,
 * logs those errors, and displays a fallback UI instead of crashing the app.
 */
class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      isRetrying: false,
      showDetails: false,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return { hasError: true, error, isRetrying: false };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    this.setState({ errorInfo });
  }

  handleRetry = (): void => {
    this.setState({ isRetrying: true }, () => {
      setTimeout(() => {
        this.setState({
          hasError: false,
          error: null,
          errorInfo: null,
          isRetrying: false,
          showDetails: false,
        });
      }, 500);
    });
  };

  toggleDetails = (): void => {
    this.setState((prev) => ({ showDetails: !prev.showDetails }));
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

            <div className="mb-4">
              <button
                type="button"
                onClick={this.toggleDetails}
                className="text-muted-foreground hover:text-foreground flex w-full items-center justify-center gap-1 text-sm transition-colors"
              >
                {this.state.showDetails ? (
                  <>
                    Hide Details <ChevronUp className="h-4 w-4" />
                  </>
                ) : (
                  <>
                    Show Details <ChevronDown className="h-4 w-4" />
                  </>
                )}
              </button>

              {this.state.showDetails && (
                <div className="bg-muted mt-3 max-h-48 overflow-auto rounded-md p-3 text-left">
                  <p className="text-destructive mb-2 text-sm font-medium">
                    {this.state.error?.name}: {this.state.error?.message}
                  </p>
                  {this.state.errorInfo?.componentStack && (
                    <pre className="text-muted-foreground whitespace-pre-wrap text-xs">
                      {this.state.errorInfo.componentStack}
                    </pre>
                  )}
                </div>
              )}
            </div>

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
