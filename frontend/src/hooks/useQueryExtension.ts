import {
  useMutation,
  DefaultError,
  UseMutationOptions,
  QueryClient,
  UseMutationResult,
  useQueryClient,
} from '@tanstack/react-query';

import {
  useQuery,
  UseQueryOptions,
  UseQueryResult,
  QueryKey,
} from '@tanstack/react-query';

import { getErrorMessage } from '@/lib/utils';

interface BackendRes<T = any> {
  success: boolean;
  error?: string;
  message?: string;
  data?: T;
}

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

  const defaultOptions = {
    retry: 2,
    retryDelay: 500,
  };

  const res = useMutation<TData, TError, TVariables, TContext>(
    {
      ...defaultOptions,
      ...options,
      onSuccess: (data, variables, context, mutationContext) => {
        options.onSuccess?.(data, variables, context, mutationContext);
      },
      onError: (error: any, variables, context, mutationContext) => {
        options.onError?.(error, variables, context, mutationContext);
      },
      onSettled: (data, error, variables, context, mutationContext) => {
        options.onSettled?.(data, error, variables, context, mutationContext);

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
    errorMessage: res.error ? getErrorMessage(res.error) : undefined,
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
  const defaultOptions = {
    retry: 2,
    retryDelay: 500,
  };

  const res = useQuery<TQueryFnData, TError, TQueryFnData, TQueryKey>({
    ...defaultOptions,
    ...options,
  });

  return {
    ...res,
    successData: res.data?.data,
    errorMessage: res.error ? getErrorMessage(res.error) : undefined,
    successMessage: res.data?.message,
  };
}
