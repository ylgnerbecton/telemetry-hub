import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Chip from "@mui/material/Chip";
import LinearProgress from "@mui/material/LinearProgress";
import Skeleton from "@mui/material/Skeleton";
import Table from "@mui/material/Table";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableContainer from "@mui/material/TableContainer";
import TableHead from "@mui/material/TableHead";
import TableRow from "@mui/material/TableRow";
import Typography from "@mui/material/Typography";

import { useVehicles } from "../api/queries";
import type { IVehicle } from "../api/types";
import { batteryColor, formatTime, statusColor } from "../format";
import { Panel } from "./Panel";

function renderBattery(vehicle: IVehicle): JSX.Element {
  if (vehicle.battery_pct === null) {
    return <span>-</span>;
  }
  return (
    <Box sx={{ display: "flex", alignItems: "center", gap: 1, minWidth: 110 }}>
      <LinearProgress
        variant="determinate"
        value={vehicle.battery_pct}
        color={batteryColor(vehicle.battery_pct)}
        sx={{ flexGrow: 1, height: 8, borderRadius: 4 }}
      />
      <Typography variant="caption" sx={{ width: 36, textAlign: "right" }}>
        {vehicle.battery_pct}%
      </Typography>
    </Box>
  );
}

function renderAnomaly(vehicle: IVehicle): string {
  if (vehicle.most_recent_anomaly === null) {
    return "-";
  }
  return `${vehicle.most_recent_anomaly.type} (${vehicle.most_recent_anomaly.severity})`;
}

export function VehicleTable(): JSX.Element {
  const { data, isLoading, isError } = useVehicles();

  if (isLoading) {
    return (
      <Panel title="Vehicles">
        <Skeleton variant="rounded" height={320} />
      </Panel>
    );
  }
  if (isError || data === undefined) {
    return (
      <Panel title="Vehicles">
        <Alert severity="error">Failed to load vehicles.</Alert>
      </Panel>
    );
  }
  if (data.vehicles.length === 0) {
    return (
      <Panel title="Vehicles">
        <Typography color="text.secondary">
          No vehicles yet. Seed the database to begin.
        </Typography>
      </Panel>
    );
  }

  return (
    <Panel title={`Vehicles (${data.vehicles.length})`}>
      <TableContainer sx={{ maxHeight: 440 }}>
        <Table size="small" stickyHeader>
          <TableHead>
            <TableRow>
              <TableCell>Vehicle</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Battery</TableCell>
              <TableCell>Speed</TableCell>
              <TableCell>Last seen</TableCell>
              <TableCell>Recent anomaly</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {data.vehicles.map((vehicle) => (
              <TableRow key={vehicle.vehicle_id} hover>
                <TableCell>{vehicle.vehicle_id}</TableCell>
                <TableCell>
                  <Chip
                    size="small"
                    color={statusColor(vehicle.current_status)}
                    label={vehicle.current_status}
                  />
                </TableCell>
                <TableCell>{renderBattery(vehicle)}</TableCell>
                <TableCell>
                  {vehicle.speed_mps === null
                    ? "-"
                    : `${vehicle.speed_mps.toFixed(1)} m/s`}
                </TableCell>
                <TableCell>{formatTime(vehicle.last_seen_at)}</TableCell>
                <TableCell>{renderAnomaly(vehicle)}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Panel>
  );
}
