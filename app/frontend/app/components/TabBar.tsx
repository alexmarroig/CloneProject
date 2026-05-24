import { ghost, panel } from "./styles";

export const tabs = ["Voice Studio", "Generate", "Convert", "Train", "Datasets", "Voices", "Models", "Jobs", "Settings"] as const;
export type Tab = (typeof tabs)[number];

type Props = {
  activeTab: Tab;
  onSelect: (tab: Tab) => void;
};

export function TabBar({ activeTab, onSelect }: Props) {
  return (
    <section style={{ ...panel, marginBottom: 14, padding: 12 }}>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
        {tabs.map((tab) => (
          <button
            key={tab}
            type="button"
            style={{
              ...ghost,
              background: activeTab === tab ? "var(--ink)" : "transparent",
              color: activeTab === tab ? "white" : "var(--ink)",
            }}
            onClick={() => onSelect(tab)}
          >
            {tab}
          </button>
        ))}
      </div>
    </section>
  );
}
