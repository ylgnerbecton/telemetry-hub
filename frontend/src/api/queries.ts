import { useInfiniteQuery, useQuery } from "@tanstack/react-query";
import type {
  InfiniteData,
  UseInfiniteQueryResult,
  UseQueryResult,
} from "@tanstack/react-query";

import { POLL_INTERVALS } from "../config";
import {
  fetchAnomalies,
  fetchFleetState,
  fetchHealth,
  fetchVehicles,
  fetchZoneCounts,
} from "./client";
import type {
  IAnomaliesPage,
  IFleetState,
  IHealth,
  IVehiclesResponse,
  IZonesResponse,
} from "./types";

export function useHealth(): UseQueryResult<IHealth, Error> {
  return useQuery({
    queryKey: ["health"],
    queryFn: fetchHealth,
    refetchInterval: POLL_INTERVALS.health,
  });
}

export function useFleetState(): UseQueryResult<IFleetState, Error> {
  return useQuery({
    queryKey: ["fleetState"],
    queryFn: fetchFleetState,
    refetchInterval: POLL_INTERVALS.fleetState,
  });
}

export function useVehicles(): UseQueryResult<IVehiclesResponse, Error> {
  return useQuery({
    queryKey: ["vehicles"],
    queryFn: fetchVehicles,
    refetchInterval: POLL_INTERVALS.vehicles,
  });
}

export function useZoneCounts(): UseQueryResult<IZonesResponse, Error> {
  return useQuery({
    queryKey: ["zoneCounts"],
    queryFn: fetchZoneCounts,
    refetchInterval: POLL_INTERVALS.zoneCounts,
  });
}

export function useAnomalies(): UseInfiniteQueryResult<
  InfiniteData<IAnomaliesPage, string | null>,
  Error
> {
  return useInfiniteQuery({
    queryKey: ["anomalies"],
    queryFn: ({ pageParam }) => fetchAnomalies(pageParam),
    initialPageParam: null as string | null,
    getNextPageParam: (lastPage) => lastPage.next_cursor ?? undefined,
    refetchInterval: POLL_INTERVALS.anomalies,
  });
}
