import AppBar from "@mui/material/AppBar";
import Box from "@mui/material/Box";
import Container from "@mui/material/Container";
import CssBaseline from "@mui/material/CssBaseline";
import Stack from "@mui/material/Stack";
import Toolbar from "@mui/material/Toolbar";
import Typography from "@mui/material/Typography";
import { ThemeProvider } from "@mui/material/styles";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { AnomalyPanel } from "./components/AnomalyPanel";
import { FleetSummary } from "./components/FleetSummary";
import { HealthIndicator } from "./components/HealthIndicator";
import { VehicleTable } from "./components/VehicleTable";
import { ZoneCounts } from "./components/ZoneCounts";
import { theme } from "./theme";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
    },
  },
});

export default function App(): JSX.Element {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <AppBar position="static" color="default" elevation={1}>
          <Toolbar sx={{ justifyContent: "space-between" }}>
            <Typography variant="h6" fontWeight={700}>
              Telemetry Hub
            </Typography>
            <HealthIndicator />
          </Toolbar>
        </AppBar>
        <Container maxWidth="lg" sx={{ py: 3 }}>
          <Stack spacing={3}>
            <FleetSummary />
            <VehicleTable />
            <Box
              sx={{
                display: "grid",
                gridTemplateColumns: { xs: "1fr", md: "1fr 1fr" },
                gap: 3,
              }}
            >
              <ZoneCounts />
              <AnomalyPanel />
            </Box>
          </Stack>
        </Container>
      </ThemeProvider>
    </QueryClientProvider>
  );
}
