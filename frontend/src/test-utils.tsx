import React, { ReactElement } from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { Provider } from 'react-redux';
import { ThemeProvider } from '@/contexts/ThemeContext';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router';
import { configureStore } from '@reduxjs/toolkit';
import { rootReducer, RootState } from '@/app/store';

interface CustomRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  preloadedState?: Partial<RootState>;
  store?: ReturnType<typeof configureStore>;
  initialRoutes?: string[];
}

const AllTheProviders = ({
  children,
  store,
  initialRoutes = ['/'],
}: {
  children: React.ReactNode;
  store: ReturnType<typeof configureStore>;
  initialRoutes?: string[];
}) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  return (
    <Provider store={store}>
      <ThemeProvider>
        <QueryClientProvider client={queryClient}>
          <MemoryRouter initialEntries={initialRoutes}>{children}</MemoryRouter>
        </QueryClientProvider>
      </ThemeProvider>
    </Provider>
  );
};

const customRender = (ui: ReactElement, options?: CustomRenderOptions) => {
  const { store, initialRoutes, preloadedState, ...renderOptions } =
    options || {};

  const testStore =
    store ??
    configureStore({
      reducer: rootReducer,
      preloadedState,
    });

  return render(ui, {
    wrapper: (props) => (
      <AllTheProviders
        {...props}
        store={testStore}
        initialRoutes={initialRoutes}
      />
    ),
    ...renderOptions,
  });
};

// Re-export everything
export * from '@testing-library/react';
export { customRender as render };
