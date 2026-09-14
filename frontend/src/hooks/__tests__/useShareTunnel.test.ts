import { act, renderHook, waitFor } from '@testing-library/react';
import { startTunnel, stopTunnel, tunnelStatus } from '@/utils/tunnel';
import { useShareTunnel } from '../useShareTunnel';

jest.mock('@/utils/tunnel', () => ({
  startTunnel: jest.fn(),
  stopTunnel: jest.fn(),
  tunnelStatus: jest.fn(),
}));

const mockStartTunnel = startTunnel as jest.Mock;
const mockStopTunnel = stopTunnel as jest.Mock;
const mockTunnelStatus = tunnelStatus as jest.Mock;

describe('useShareTunnel', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockStartTunnel.mockResolvedValue('https://abc123.lhr.life');
    mockStopTunnel.mockResolvedValue(undefined);
    mockTunnelStatus.mockResolvedValue(null);
  });

  it('reports the address it opened', async () => {
    const { result } = renderHook(() => useShareTunnel());

    await act(async () => {
      await result.current.open(52125);
    });

    expect(mockStartTunnel).toHaveBeenCalledWith(52125);
    expect(result.current.url).toBe('https://abc123.lhr.life');
  });

  // Stopping while a tunnel is still opening must not leave a live public
  // address behind once the slow start finally answers.
  it('closes a tunnel that finished opening after it was stopped', async () => {
    let settleStart: (value: string) => void = () => undefined;
    mockStartTunnel.mockReturnValueOnce(
      new Promise<string>((resolve) => {
        settleStart = resolve;
      }),
    );

    const { result } = renderHook(() => useShareTunnel());

    let opening: Promise<string> = Promise.resolve('');
    act(() => {
      opening = result.current.open(52125);
      opening.catch(() => undefined);
    });

    await act(async () => {
      await result.current.close();
    });

    await act(async () => {
      settleStart('https://late.lhr.life');
      await expect(opening).rejects.toThrow(/closed while it was starting/i);
    });

    expect(result.current.url).toBeNull();
    // Twice: once for the close, once for the tunnel that arrived too late.
    expect(mockStopTunnel).toHaveBeenCalledTimes(2);
  });

  // Asking first would read null while a start is still in flight and skip the
  // stop, leaving the child the owner already holds.
  it('asks for a stop without checking whether one is running', async () => {
    const { result } = renderHook(() => useShareTunnel());

    await act(async () => {
      await result.current.close();
    });

    expect(mockStopTunnel).toHaveBeenCalled();
    expect(mockTunnelStatus).not.toHaveBeenCalled();
  });

  it('lets a failed stop reach the caller', async () => {
    mockStopTunnel.mockRejectedValue(
      new Error('ssh pid 900 may still be running'),
    );
    const { result } = renderHook(() => useShareTunnel());

    await act(async () => {
      await expect(result.current.close()).rejects.toThrow(
        /may still be running/i,
      );
    });
  });

  it('ignores a status lookup that answers after a tunnel was opened', async () => {
    let settleStatus: (value: string | null) => void = () => undefined;
    mockTunnelStatus.mockReturnValueOnce(
      new Promise<string | null>((resolve) => {
        settleStatus = resolve;
      }),
    );

    const { result } = renderHook(() => useShareTunnel());

    let refreshing: Promise<string | null> = Promise.resolve(null);
    act(() => {
      refreshing = result.current.refresh();
    });
    await act(async () => {
      await result.current.open(52125);
    });

    await act(async () => {
      settleStatus(null);
      await refreshing;
    });

    await waitFor(() =>
      expect(result.current.url).toBe('https://abc123.lhr.life'),
    );
  });
});
