import React from 'react';
import { act, screen, fireEvent } from '@testing-library/react';
import { useLocation } from 'react-router';
import { render } from '@/test-utils';
import {
  MemoryNotificationListener,
  type PendingMemory,
} from '../MemoryNotificationListener';

type Handler = (event: { payload: unknown }) => void;

const handlers: Record<string, Handler> = {};
const mockUnlisten = jest.fn();
const mockInvoke = jest.fn();

jest.mock('@tauri-apps/api/event', () => ({
  listen: jest.fn((name: string, handler: Handler) => {
    handlers[name] = handler;
    return Promise.resolve(mockUnlisten);
  }),
}));

jest.mock('@tauri-apps/api/core', () => ({
  invoke: (...args: unknown[]) => mockInvoke(...args),
}));

const pending: PendingMemory = {
  memory_id: 'mem-9',
  title: 'Beach',
  subtitle: '11 July 2026',
  image_count: 9,
  video_count: 1,
};

/** Reports the current route, so navigation is observable. */
const Probe: React.FC = () => (
  <div data-testid="path">{useLocation().pathname}</div>
);

const renderListener = () =>
  render(
    <>
      <MemoryNotificationListener />
      <Probe />
    </>,
  );

const emit = (name: string, payload: unknown) =>
  act(() => {
    handlers[name]({ payload });
  });

beforeEach(() => {
  mockInvoke.mockReset().mockResolvedValue(null);
  mockUnlisten.mockClear();
});

describe('MemoryNotificationListener', () => {
  it('shows nothing until a memory is announced', () => {
    renderListener();
    expect(screen.queryByRole('status')).not.toBeInTheDocument();
  });

  it('surfaces the card when the desktop task announces a memory', () => {
    renderListener();
    emit('memory:pending', pending);

    expect(screen.getByText('Your Daily Memory is Ready')).toBeInTheDocument();
    expect(
      screen.getByText('Beach · 11 July 2026 · 10 items'),
    ).toBeInTheDocument();
  });

  it('routes through the open_memory command when the card is clicked', () => {
    renderListener();
    emit('memory:pending', pending);

    fireEvent.click(screen.getByRole('button', { name: 'View memory' }));

    expect(mockInvoke).toHaveBeenCalledWith('open_memory', {
      memoryId: 'mem-9',
    });
  });

  it('opens the viewer on memory:open', () => {
    const { store } = renderListener();
    emit('memory:pending', pending);
    emit('memory:open', { memory_id: 'mem-9' });

    expect(store.getState().memories.activeMemoryId).toBe('mem-9');
    expect(screen.getByTestId('path')).toHaveTextContent('/memories');
    // The card has done its job; leaving it over the viewer would be noise.
    expect(screen.queryByText('Your Daily Memory is Ready')).toBeNull();
  });

  // Outside the desktop shell there is no command to invoke, and the card
  // would otherwise do nothing at all.
  it('falls back to routing here when the command is unavailable', async () => {
    mockInvoke.mockRejectedValue(new Error('no such command'));
    const { store } = renderListener();
    emit('memory:pending', pending);

    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: 'View memory' }));
    });

    expect(store.getState().memories.activeMemoryId).toBe('mem-9');
    expect(screen.getByTestId('path')).toHaveTextContent('/memories');
  });

  it('dismisses without opening anything', () => {
    const { store } = renderListener();
    emit('memory:pending', pending);

    fireEvent.click(
      screen.getByRole('button', { name: 'Dismiss memory notification' }),
    );

    expect(screen.queryByText('Your Daily Memory is Ready')).toBeNull();
    expect(store.getState().memories.activeMemoryId).toBeNull();
  });

  it('unsubscribes both listeners on unmount', async () => {
    const { unmount } = renderListener();
    unmount();
    await act(async () => {});

    expect(mockUnlisten).toHaveBeenCalledTimes(2);
  });
});
