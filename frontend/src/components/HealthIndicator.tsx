import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import ErrorIcon from "@mui/icons-material/Error";
import Chip from "@mui/material/Chip";

import { useHealth } from "../api/queries";

export function HealthIndicator(): JSX.Element {
  const { data, isError } = useHealth();
  const isOnline = !isError && data?.status === "ok";
  return (
    <Chip
      color={isOnline ? "success" : "error"}
      icon={isOnline ? <CheckCircleIcon /> : <ErrorIcon />}
      label={isOnline ? "API online" : "API offline"}
      size="small"
    />
  );
}
