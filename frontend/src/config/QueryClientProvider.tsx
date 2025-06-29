import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React, { useState } from 'react';

const QueryClientProviders = ({ children }: { children: React.ReactNode }) => {
  const [queryClient] = useState(() => new QueryClient());
  return (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

export default QueryClientProviders;
