import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { FilterBar } from '../components/FilterBar';

describe('FilterBar', () => {
  it('debounces and emits filter changes', async () => {
    const onChange = vi.fn();
    render(<FilterBar initial={{}} onChange={onChange} />);
    fireEvent.change(screen.getByDisplayValue(''), { target: { value: 'v1.2' } });
    await waitFor(() => expect(onChange).toHaveBeenCalled(), { timeout: 600 });
    expect(onChange.mock.calls.at(-1)![0]).toMatchObject({ prompt_version: 'v1.2' });
  });
});
