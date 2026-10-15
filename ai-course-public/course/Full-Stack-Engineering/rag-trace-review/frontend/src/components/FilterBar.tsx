import { useEffect, useState } from 'react';
import type { TraceFilters } from '../types';

interface Props {
  initial: TraceFilters;
  onChange: (f: TraceFilters) => void;
}

export function FilterBar({ initial, onChange }: Props) {
  const [day, setDay] = useState(initial.day ?? '');
  const [pv, setPv] = useState(initial.prompt_version ?? '');
  const [min, setMin] = useState<string>(initial.min_latency?.toString() ?? '');
  const [max, setMax] = useState<string>(initial.max_latency?.toString() ?? '');

  useEffect(() => {
    const t = setTimeout(() => {
      onChange({
        day: day || undefined,
        prompt_version: pv || undefined,
        min_latency: min ? Number(min) : undefined,
        max_latency: max ? Number(max) : undefined,
      });
    }, 300);
    return () => clearTimeout(t);
  }, [day, pv, min, max, onChange]);

  return (
    <div className="flex flex-wrap gap-3 p-3 bg-gray-50 rounded items-end" role="search">
      <label className="flex flex-col text-xs">
        Day
        <input
          type="date"
          className="border rounded p-1"
          value={day}
          onChange={(e) => setDay(e.target.value)}
        />
      </label>
      <label className="flex flex-col text-xs">
        Prompt version
        <select
          className="border rounded p-1"
          value={pv}
          onChange={(e) => setPv(e.target.value)}
        >
          <option value="">All</option>
          <option value="v1.0">v1.0</option>
          <option value="v1.1">v1.1</option>
          <option value="v1.2">v1.2</option>
          <option value="v2.0">v2.0</option>
        </select>
      </label>
      <label className="flex flex-col text-xs">
        Min latency (ms)
        <input
          type="number"
          className="border rounded p-1 w-24"
          value={min}
          onChange={(e) => setMin(e.target.value)}
        />
      </label>
      <label className="flex flex-col text-xs">
        Max latency (ms)
        <input
          type="number"
          className="border rounded p-1 w-24"
          value={max}
          onChange={(e) => setMax(e.target.value)}
        />
      </label>
    </div>
  );
}
