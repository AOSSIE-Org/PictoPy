import { isIndexingPending } from '@/types/Folder';

describe('isIndexingPending', () => {
  it.each(['not_started', 'in_progress'] as const)(
    'treats %s as work in flight',
    (status) => {
      expect(isIndexingPending(status)).toBe(true);
    },
  );

  it('treats a finished walk as settled', () => {
    expect(isIndexingPending('completed')).toBe(false);
  });

  it('treats an interrupted walk as settled', () => {
    // A previous session died mid-walk. Nothing is running, so a spinner here
    // would wait on a walk nobody is going to start.
    expect(isIndexingPending('interrupted')).toBe(false);
  });

  it('treats a missing status as pending, as the old check did', () => {
    expect(isIndexingPending(undefined)).toBe(true);
  });
});
