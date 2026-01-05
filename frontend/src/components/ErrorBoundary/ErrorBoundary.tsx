import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

/**
 * Error Boundary component that catches JavaScript errors anywhere in the
 * child component tree and displays a fallback UI instead of crashing the app.
 *
 * Reference: https://react.dev/reference/react/Component#catching-rendering-errors-with-an-error-boundary
 */
class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    // Update state so the next render shows the fallback UI
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    // Log error details for debugging
    console.error('ErrorBoundary caught an error:', error);
    console.error('Error info:', errorInfo);

    this.setState({
      error,
      errorInfo,
    });
  }

  handleReload = (): void => {
    // Reset error state and reload the page
    this.setState({ hasError: false, error: null, errorInfo: null });
    window.location.reload();
  };

  handleReset = (): void => {
    // Reset error state without reloading (try to recover)
    this.setState({ hasError: false, error: null, errorInfo: null });
  };

  render(): ReactNode {
    if (this.state.hasError) {
      return (
        <div className="flex min-h-screen items-center justify-center bg-gray-50 p-4 dark:bg-gray-900">
          <div className="w-full max-w-md rounded-lg border border-gray-200 bg-white p-6 shadow-lg dark:border-gray-700 dark:bg-gray-800">
            {/* Error Icon */}
            <div className="mb-4 flex justify-center">
              <div className="flex h-16 w-16 items-center justify-center rounded-full bg-red-100 dark:bg-red-900/30">
                <AlertTriangle className="h-8 w-8 text-red-600 dark:text-red-400" />
              </div>
            </div>

            {/* Error Title */}
            <h1 className="mb-2 text-center text-xl font-semibold text-gray-900 dark:text-white">
              Something went wrong
            </h1>

            {/* Error Description */}
            <p className="mb-4 text-center text-sm text-gray-600 dark:text-gray-400">
              An unexpected error occurred. Please try reloading the
              application.
            </p>

            {/* Error Details (collapsible) */}
            {this.state.error && (
              <details className="mb-4 rounded-md bg-gray-100 p-3 dark:bg-gray-700">
                <summary className="cursor-pointer text-sm font-medium text-gray-700 dark:text-gray-300">
                  Error Details
                </summary>
                <div className="mt-2 space-y-2">
                  <p className="break-words text-xs text-red-600 dark:text-red-400">
                    {this.state.error.toString()}
                  </p>
                  {this.state.errorInfo && (
                    <pre className="max-h-32 overflow-auto whitespace-pre-wrap text-xs text-gray-600 dark:text-gray-400">
                      {this.state.errorInfo.componentStack}
                    </pre>
                  )}
                </div>
              </details>
            )}

            {/* Action Buttons */}
            <div className="flex flex-col gap-2 sm:flex-row">
              <button
                onClick={this.handleReload}
                className="flex flex-1 items-center justify-center gap-2 rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
              >
                <RefreshCw className="h-4 w-4" />
                Reload Application
              </button>
              <button
                onClick={this.handleReset}
                className="flex flex-1 items-center justify-center gap-2 rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600"
              >
                Try Again
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
