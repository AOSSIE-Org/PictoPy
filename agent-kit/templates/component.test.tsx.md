# Template: `frontend/src/components/__tests__/<Name>.test.tsx`

Copy and adapt. Modelled on the existing tests in `frontend/src/components/__tests__/`.

```tsx
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MyComponent } from '@/components/Area/MyComponent';

describe('MyComponent', () => {
  it('renders the provided items', () => {
    render(<MyComponent items={[{ id: '1', name: 'First' }]} />);

    expect(screen.getByText('First')).toBeInTheDocument();
  });

  it('shows the empty state when there are no items', () => {
    render(<MyComponent items={[]} />);

    expect(screen.getByText(/nothing here/i)).toBeInTheDocument();
  });

  it('calls onSelect when an item is clicked', async () => {
    const onSelect = jest.fn();
    render(<MyComponent items={[{ id: '1', name: 'First' }]} onSelect={onSelect} />);

    await userEvent.click(screen.getByText('First'));

    expect(onSelect).toHaveBeenCalledWith('1');
  });
});
```

For a component that reads from the store, use the helpers in `frontend/src/test-utils.tsx`
rather than wrapping in a `Provider` by hand.

## Notes

- Assert on what the user sees — `getByText`, `getByRole` — not on props, state, or
  internal function calls.
- **Always test the empty state.** It is the case this codebase has regressed on before,
  which is why `EmptyStates.test.tsx` exists.
- Prefer `userEvent` over `fireEvent`; it models real interaction more closely.
- `jest.setup.ts` already wires up `@testing-library/jest-dom`, so matchers like
  `toBeInTheDocument` are available without importing them.
- Mocks for static assets and modules live in `frontend/__mocks__/`.
- No `TODO` or `FIXME` comments — ESLint fails the build on them, tests included.
