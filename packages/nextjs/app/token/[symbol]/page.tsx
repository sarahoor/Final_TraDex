import PriceChart from '@/components/token/chart/PriceChart';

export default async function Page(props: { params: Promise<{ symbol: string }> }) {
  const { symbol } = await props.params;
  return (
    <main className="inset-0 bg-base-100">
      <PriceChart symbol={symbol} />
    </main>
  );
}