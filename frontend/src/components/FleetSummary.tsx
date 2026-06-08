import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Skeleton from "@mui/material/Skeleton";
import Typography from "@mui/material/Typography";

import { useFleetState } from "../api/queries";
import { Panel } from "./Panel";

export function FleetSummary(): JSX.Element {
  const { data, isLoading, isError } = useFleetState();

  if (isLoading) {
    return (
      <Panel title="Fleet Summary">
        <Skeleton variant="rounded" height={96} />
      </Panel>
    );
  }
  if (isError || data === undefined) {
    return (
      <Panel title="Fleet Summary">
        <Alert severity="error">Failed to load fleet summary.</Alert>
      </Panel>
    );
  }

  const tiles = [
    { label: "Total", value: data.total },
    { label: "Idle", value: data.by_status.idle },
    { label: "Moving", value: data.by_status.moving },
    { label: "Charging", value: data.by_status.charging },
    { label: "Fault", value: data.by_status.fault },
  ];

  return (
    <Panel title="Fleet Summary">
      <Box
        sx={{
          display: "grid",
          gridTemplateColumns: { xs: "repeat(2, 1fr)", sm: "repeat(5, 1fr)" },
          gap: 2,
        }}
      >
        {tiles.map((tile) => (
          <Box
            key={tile.label}
            sx={{
              textAlign: "center",
              py: 2,
              borderRadius: 2,
              bgcolor: "action.hover",
            }}
          >
            <Typography variant="h4" component="div" fontWeight={700}>
              {tile.value}
            </Typography>
            <Typography variant="overline" color="text.secondary">
              {tile.label}
            </Typography>
          </Box>
        ))}
      </Box>
    </Panel>
  );
}
