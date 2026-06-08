import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Chip from "@mui/material/Chip";
import List from "@mui/material/List";
import ListItem from "@mui/material/ListItem";
import Skeleton from "@mui/material/Skeleton";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import { useAnomalies } from "../api/queries";
import type { IAnomaly } from "../api/types";
import { formatTime, severityColor } from "../format";
import { Panel } from "./Panel";

function flattenUnique(pages: { items: IAnomaly[] }[]): IAnomaly[] {
  const seen = new Set<string>();
  const anomalies: IAnomaly[] = [];
  for (const page of pages) {
    for (const anomaly of page.items) {
      if (!seen.has(anomaly.id)) {
        seen.add(anomaly.id);
        anomalies.push(anomaly);
      }
    }
  }
  return anomalies;
}

export function AnomalyPanel(): JSX.Element {
  const {
    data,
    isLoading,
    isError,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = useAnomalies();

  if (isLoading) {
    return (
      <Panel title="Recent Anomalies">
        <Skeleton variant="rounded" height={320} />
      </Panel>
    );
  }
  if (isError || data === undefined) {
    return (
      <Panel title="Recent Anomalies">
        <Alert severity="error">Failed to load anomalies.</Alert>
      </Panel>
    );
  }

  const anomalies = flattenUnique(data.pages);

  if (anomalies.length === 0) {
    return (
      <Panel title="Recent Anomalies">
        <Typography color="text.secondary">No anomalies detected.</Typography>
      </Panel>
    );
  }

  return (
    <Panel title="Recent Anomalies">
      <Box sx={{ maxHeight: 360, overflowY: "auto" }}>
        <List dense disablePadding>
          {anomalies.map((anomaly) => (
            <ListItem
              key={anomaly.id}
              divider
              disableGutters
              sx={{ display: "block", px: 0.5 }}
            >
              <Stack direction="row" spacing={1} alignItems="center">
                <Typography variant="body2" component="span" fontWeight={700}>
                  {anomaly.vehicle_id}
                </Typography>
                <Chip
                  size="small"
                  color={severityColor(anomaly.severity)}
                  label={anomaly.severity}
                />
                <Typography
                  variant="caption"
                  component="span"
                  color="text.secondary"
                  sx={{ ml: "auto" }}
                >
                  {formatTime(anomaly.observed_at)}
                </Typography>
              </Stack>
              <Typography
                variant="caption"
                component="div"
                color="text.secondary"
              >
                {anomaly.type}: {anomaly.message}
              </Typography>
            </ListItem>
          ))}
        </List>
      </Box>
      <Box sx={{ mt: 1, textAlign: "center" }}>
        <Button
          size="small"
          onClick={() => {
            void fetchNextPage();
          }}
          disabled={!hasNextPage || isFetchingNextPage}
        >
          {isFetchingNextPage
            ? "Loading..."
            : hasNextPage
              ? "Load older"
              : "No more anomalies"}
        </Button>
      </Box>
    </Panel>
  );
}
