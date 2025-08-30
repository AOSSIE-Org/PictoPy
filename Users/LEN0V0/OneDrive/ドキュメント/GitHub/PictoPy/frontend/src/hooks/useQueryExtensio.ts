import {
  useMutation,
  DefaultError,
  UseMutationOptions,
  QueryClient,
  UseMutationResult,
  useQuery,
  UseQueryOptions,
  UseQueryResult,
  QueryKey,
  useQueryClient,
} from '@tanstack/react-query';

// Updated BackendRes to match the new response structure
interface BackendRes<T = any> {
  success: boolean;
  error?: string;
  message?: string;
  data?: T;
}

// Initialize query client with persistence
export const queryClient = new QueryClient();

// Custom useSTMutation hook
export function usePictoMutation<
  TData extends BackendRes<TSuccessData>,
  TError = DefaultError,
  TVariables = any,
  TContext = unknown,
  TSuccessData = any,
>(
  options: UseMutationOptions<TData, TError, TVariables, TContext> & {
    autoInvalidateTags?: string[];
  },
  queryClient?: QueryClient,
): UseMutationResult<TData, TError, TVariables, TContext> & {
  successData: TSuccessData | undefined;
  errorMessage: string | undefined;
  successMessage: string | undefined;
} {
  const myQueryClient = useQueryClient();

  const res = useMutation<TData, TError, TVariables, TContext>(
    {
      ...options,
      onSuccess: (data, variables, context) => {
        if (options.onSuccess) {
          options.onSuccess(data, variables, context);
        }
      },
      onError: (error: any, variables, context) => {
        if (options.onError) {
          options.onError(error, variables, context);
        }
      },
      onSettled: (data, error, variables, context) => {
        if (options.onSettled) {
          options.onSettled(data, error, variables, context);
        }

        if (options.autoInvalidateTags) {
          myQueryClient.invalidateQueries({
            queryKey: options.autoInvalidateTags,
          });
        }
      },
    },
    queryClient,
  );

  return {
    ...res,
    successData: res.data?.data,
    errorMessage: res.data?.error || 'Something went wrong',
    successMessage: res.data?.message,
  };
}

export function usePictoQuery<
  TQueryFnData extends BackendRes<TSuccessData>,
  TError = unknown,
  TSuccessData = any,
  TQueryKey extends QueryKey = QueryKey,
>(
  options: UseQueryOptions<TQueryFnData, TError, TQueryFnData, TQueryKey>,
): UseQueryResult<TQueryFnData, TError> & {
  successData: TSuccessData | undefined;
  errorMessage: string | undefined;
  successMessage: string | undefined;
} {
  const res = useQuery<TQueryFnData, TError, TQueryFnData, TQueryKey>(options);

  return {
    ...res,
    successData: res.data?.data,
    errorMessage: res.data?.error || 'Something went wrong',
    successMessage: res.data?.message,
  };
}
