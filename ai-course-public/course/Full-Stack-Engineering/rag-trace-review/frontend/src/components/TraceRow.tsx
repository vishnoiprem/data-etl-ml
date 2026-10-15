import { useRef } from 'react';
import { useVirtualizer } from '@tanstack/react-virtual';
import type { TraceSummary } from '../types';

interface Props {
  rows: TraceSummary[];
  onSelect: (id: string) => void;
  selectedId?: string;
}

export function TraceTable({ rows, onSelect, selectedId }: Props) {
  const parentRef = useRef<HTMLDivElement>(null);
  const virt = useVirtualizer({
    count: rows.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 44,
    overscan: 8,
  });

  if (rows.length === 0) {
    return (
      <div className="p-8 text-center text-gray-500" role="status">
        No traces match the current filters.
      </div>
    );
  }

  return (
    <div
      ref={parentRef}
      className="h-[70vh] overflow-auto border rounded"
      data-testid="trace-table-scroll"
    >
      <table className="w-full text-sm">
        <thead className="bg-gray-50 sticky top-0 z-10">
          <tr>
            <th className="p-2 text-left">Trace</th>
            <th className="p-2 text-left">Created</th>
            <th className="p-2 text-left">Prompt</th>
            <th className="p-2 text-left">Query</th>
            <th className="p-2 text-right">Tokens</th>
            <th className="p-2 text-right">Latency</th>
            <th className="p-2 text-left">Status</th>
            <th className="p-2 text-left">Feedback</th>
          </tr>
        </thead>
        <tbody style={{ height: virt.getTotalSize(), position: 'relative' }}>
          {virt.getVirtualItems().map((vi) => {
            const t = rows[vi.index];
            return (
              <tr
                key={t.trace_id}
                onClick={() => onSelect(t.trace_id)}
                style={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  width: '100%',
                  height: vi.size,
                  transform: `translateY(${vi.start}px)`,
                  background: selectedId === t.trace_id ? '#eef' : 'white',
                  cursor: 'pointer',
                }}
                data-testid={`row-${t.trace_id}`}
              >
                <td className="p-2 font-mono text-xs">{t.trace_id}</td>
                <td className="p-2">{t.created_at.slice(0, 16).replace('T', ' ')}</td>
                <td className="p-2">{t.prompt_version}</td>
                <td className="p-2 truncate max-w-xs">{t.user_query}</td>
                <td className="p-2 text-right">{t.token_usage}</td>
                <td className="p-2 text-right">{t.latency_ms}ms</td>
                <td className="p-2">
                  <span
                    className={
                      t.status === 'ok'
                        ? 'text-green-600'
                        : 'text-red-600 font-semibold'
                    }
                  >
                    {t.status}
                  </span>
                </td>
                <td className="p-2">
                  {t.feedback === 'up' && '👍'}
                  {t.feedback === 'down' && '👎'}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
