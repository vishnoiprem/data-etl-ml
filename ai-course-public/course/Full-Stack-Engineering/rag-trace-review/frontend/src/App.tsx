import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { TraceList } from './pages/TraceList';

const qc = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, refetchOnWindowFocus: false, staleTime: 30_000 },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={qc}>
      <TraceList />
    </QueryClientProvider>
  );
}
