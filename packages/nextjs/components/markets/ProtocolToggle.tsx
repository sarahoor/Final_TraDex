"use client";

export default function ProtocolToggle({
  enabled,
  onChange,
}: {
  enabled: { uni: boolean; sushi: boolean; quick: boolean; cake: boolean };
  onChange: (v: { uni: boolean; sushi: boolean; quick: boolean; cake: boolean }) => void;
}) {
  const Item = (k: keyof typeof enabled, label: string) => (
    <label className="flex items-center gap-2 text-sm" key={k}>
      <input type="checkbox" checked={enabled[k]} onChange={e => onChange({ ...enabled, [k]: e.target.checked })} />
      {label}
    </label>
  );

  return (
    <div className="flex gap-3 flex-wrap">
      {Item("uni", "Uniswap v3 (ETH)")}
      {Item("sushi", "Sushiswap v3 (ETH)")}
      {Item("quick", "QuickSwap v3 (Polygon)")}
      {Item("cake", "Pancake v3 (BNB)")}
    </div>
  );
}
