import type { Dashboard } from '@/types/bank';

interface Props {
  data: Dashboard['radar'];
}

export function AbilityRadar({ data }: Props) {
  return (
    <div className="radar" aria-label="能力雷达图">
      {data.map((item) => (
        <div className="radar-row" key={item.axis}>
          <span>{item.axis}</span>
          <div className="radar-track">
            <i style={{ width: `${item.value}%` }} />
          </div>
          <strong>{item.value}</strong>
        </div>
      ))}
    </div>
  );
}
