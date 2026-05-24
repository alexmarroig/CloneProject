import { Health } from "../types";
import { panel } from "./styles";

type Props = {
  health: Health | null;
};

export function StudioStatusPanel({ health }: Props) {
  return (
    <section style={panel}>
      <div>
        Status: {health?.status} | Device: {health?.device} | ffmpeg: {String(health?.ffmpeg_available)} | xtts:{" "}
        {String(health?.xtts_env_available)} | rvc: {String(health?.rvc_env_available)}
      </div>
    </section>
  );
}
