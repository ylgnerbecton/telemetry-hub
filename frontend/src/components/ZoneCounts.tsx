import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import LinearProgress from "@mui/material/LinearProgress";
import Skeleton from "@mui/material/Skeleton";
import Typography from "@mui/material/Typography";

import { useZoneCounts } from "../api/queries";
import { Panel } from "./Panel";

export function ZoneCounts(): JSX.Element {
  const { data, isLoading, isError } = useZoneCounts();

  if (isLoading) {
    return (
      <Panel title="Zone Entry Counts">
        <Skeleton variant="rounded" height={320} />
      </Panel>
    );
  }
  if (isError || data === undefined) {
    return (
      <Panel title="Zone Entry Counts">
        <Alert severity="error">Failed to load zone counts.</Alert>
      </Panel>
    );
  }

  const maxCount = Math.max(1, ...data.zones.map((zone) => zone.entry_count));

  return (
    <Panel title="Zone Entry Counts">
      <Box
        sx={{
          display: "grid",
          gridTemplateColumns: { xs: "1fr", sm: "1fr 1fr" },
          columnGap: 3,
          rowGap: 1.25,
        }}
      >
        {data.zones.map((zone) => (
          <Box key={zone.zone_id}>
            <Box
              sx={{
                display: "flex",
                justifyContent: "space-between",
                mb: 0.25,
              }}
            >
              <Typography variant="body2">{zone.zone_id}</Typography>
              <Typography variant="body2" fontWeight={700}>
                {zone.entry_count}
              </Typography>
            </Box>
            <LinearProgress
              variant="determinate"
              value={(zone.entry_count / maxCount) * 100}
              sx={{ height: 6, borderRadius: 3 }}
            />
          </Box>
        ))}
      </Box>
    </Panel>
  );
}
