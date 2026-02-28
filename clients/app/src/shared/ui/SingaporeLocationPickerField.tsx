import { useEffect, useMemo, useState } from "react";
import {
  ActivityIndicator,
  Image,
  LayoutChangeEvent,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View
} from "react-native";

import { buttonStyles, palette, textStyles, typography } from "./theme";

interface LocationValue {
  lat: number;
  lng: number;
  address: string;
}

interface SingaporeLocationPickerFieldProps {
  label: string;
  value: LocationValue;
  onChange: (next: LocationValue) => void;
  hint?: string;
  error?: string;
}

interface NominatimResult {
  display_name: string;
  lat: string;
  lon: string;
}

interface SearchSuggestion {
  address: string;
  lat: number;
  lng: number;
}

const SG_CENTER = { lat: 1.3521, lng: 103.8198 } as const;
const SG_BOUNDS = {
  minLat: 1.15,
  maxLat: 1.5,
  minLng: 103.55,
  maxLng: 104.1
} as const;

const TILE_SIZE = 256;

function clamp(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value));
}

function clampToSingapore(lat: number, lng: number): { lat: number; lng: number } {
  return {
    lat: clamp(lat, SG_BOUNDS.minLat, SG_BOUNDS.maxLat),
    lng: clamp(lng, SG_BOUNDS.minLng, SG_BOUNDS.maxLng)
  };
}

function toWorldPixel(lat: number, lng: number, zoom: number): { x: number; y: number } {
  const scale = TILE_SIZE * 2 ** zoom;
  const x = ((lng + 180) / 360) * scale;
  const sinLat = Math.sin((lat * Math.PI) / 180);
  const y = (0.5 - Math.log((1 + sinLat) / (1 - sinLat)) / (4 * Math.PI)) * scale;
  return { x, y };
}

function toLatLng(worldX: number, worldY: number, zoom: number): { lat: number; lng: number } {
  const scale = TILE_SIZE * 2 ** zoom;
  const lng = (worldX / scale) * 360 - 180;
  const mercY = Math.PI * (1 - (2 * worldY) / scale);
  const lat = (180 / Math.PI) * Math.atan(0.5 * (Math.exp(mercY) - Math.exp(-mercY)));
  return { lat, lng };
}

function mapPointToLatLng(
  x: number,
  y: number,
  width: number,
  height: number,
  center: { lat: number; lng: number },
  zoom: number
): { lat: number; lng: number } {
  const centerWorld = toWorldPixel(center.lat, center.lng, zoom);
  const worldX = centerWorld.x - width / 2 + x;
  const worldY = centerWorld.y - height / 2 + y;
  return toLatLng(worldX, worldY, zoom);
}

function latLngToMapPoint(
  lat: number,
  lng: number,
  width: number,
  height: number,
  center: { lat: number; lng: number },
  zoom: number
): { x: number; y: number } {
  const centerWorld = toWorldPixel(center.lat, center.lng, zoom);
  const pinWorld = toWorldPixel(lat, lng, zoom);
  return {
    x: pinWorld.x - centerWorld.x + width / 2,
    y: pinWorld.y - centerWorld.y + height / 2
  };
}

function staticMapUrl(
  center: { lat: number; lng: number },
  marker: { lat: number; lng: number },
  zoom: number,
  width: number,
  height: number
): string {
  const safeWidth = clamp(Math.round(width), 320, 1024);
  const safeHeight = clamp(Math.round(height), 180, 512);
  return `https://staticmap.openstreetmap.de/staticmap.php?center=${center.lat},${center.lng}&zoom=${zoom}&size=${safeWidth}x${safeHeight}&maptype=mapnik&markers=${marker.lat},${marker.lng},red-pushpin`;
}

function fallbackAddress(lat: number, lng: number): string {
  return `Singapore (${lat.toFixed(5)}, ${lng.toFixed(5)})`;
}

export function SingaporeLocationPickerField({
  label,
  value,
  onChange,
  hint,
  error
}: SingaporeLocationPickerFieldProps): JSX.Element {
  const [query, setQuery] = useState(value.address);
  const [suggestions, setSuggestions] = useState<SearchSuggestion[]>([]);
  const [searching, setSearching] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [zoom, setZoom] = useState(11);
  const [center, setCenter] = useState(() => ({ lat: value.lat, lng: value.lng }));
  const [mapSize, setMapSize] = useState({ width: 640, height: 240 });

  useEffect(() => {
    if (value.address && value.address !== query) {
      setQuery(value.address);
    }
  }, [query, value.address]);

  useEffect(() => {
    const latDelta = Math.abs(value.lat - center.lat);
    const lngDelta = Math.abs(value.lng - center.lng);
    if (latDelta > 0.02 || lngDelta > 0.02) {
      setCenter({ lat: value.lat, lng: value.lng });
    }
  }, [center.lat, center.lng, value.lat, value.lng]);

  const marker = useMemo(
    () => clampToSingapore(value.lat, value.lng),
    [value.lat, value.lng]
  );

  const mapUrl = useMemo(
    () => staticMapUrl(center, marker, zoom, mapSize.width, mapSize.height),
    [center, marker, zoom, mapSize.width, mapSize.height]
  );

  const pinPosition = useMemo(
    () => latLngToMapPoint(marker.lat, marker.lng, mapSize.width, mapSize.height, center, zoom),
    [marker, mapSize.width, mapSize.height, center, zoom]
  );

  const applyLocation = (lat: number, lng: number, address?: string) => {
    const clamped = clampToSingapore(lat, lng);
    onChange({
      lat: clamped.lat,
      lng: clamped.lng,
      address: address?.trim() || fallbackAddress(clamped.lat, clamped.lng)
    });
  };

  const updateFromMapPoint = (x: number, y: number) => {
    const next = mapPointToLatLng(x, y, mapSize.width, mapSize.height, center, zoom);
    applyLocation(next.lat, next.lng, value.address);
  };

  const onMapLayout = (event: LayoutChangeEvent) => {
    const { width, height } = event.nativeEvent.layout;
    if (width > 0 && height > 0) {
      setMapSize({ width, height });
    }
  };

  const searchAddress = async () => {
    const trimmed = query.trim();
    if (!trimmed) {
      setSuggestions([]);
      setSearchError("Type an address or area in Singapore.");
      return;
    }

    setSearching(true);
    setSearchError(null);

    try {
      const url = `https://nominatim.openstreetmap.org/search?format=jsonv2&addressdetails=0&limit=5&countrycodes=sg&q=${encodeURIComponent(trimmed)}`;
      const response = await fetch(url, {
        headers: {
          "Accept-Language": "en"
        }
      });
      if (!response.ok) {
        throw new Error(`Nominatim request failed with ${response.status}`);
      }
      const data = (await response.json()) as NominatimResult[];
      const nextSuggestions = data
        .map((item) => ({
          address: item.display_name,
          lat: Number(item.lat),
          lng: Number(item.lon)
        }))
        .filter((item) => Number.isFinite(item.lat) && Number.isFinite(item.lng))
        .map((item) => {
          const clamped = clampToSingapore(item.lat, item.lng);
          return {
            address: item.address,
            lat: clamped.lat,
            lng: clamped.lng
          };
        });

      setSuggestions(nextSuggestions);
      if (nextSuggestions.length === 0) {
        setSearchError("No Singapore matches found. Try a specific area name.");
      }
    } catch {
      setSearchError("Address search is currently unavailable.");
      setSuggestions([]);
    } finally {
      setSearching(false);
    }
  };

  return (
    <View style={styles.wrap}>
      <Text style={styles.label}>{label}</Text>

      <View style={styles.searchRow}>
        <TextInput
          value={query}
          onChangeText={setQuery}
          style={styles.searchInput}
          placeholder="Search your home address in Singapore"
          placeholderTextColor={palette.textTertiary}
          autoCapitalize="words"
          autoCorrect={false}
          onSubmitEditing={searchAddress}
        />
        <Pressable style={styles.searchBtn} onPress={searchAddress} accessibilityRole="button" disabled={searching}>
          {searching ? <ActivityIndicator color={palette.accentTextOn} /> : <Text style={styles.searchLabel}>Search</Text>}
        </Pressable>
      </View>

      {searchError ? <Text style={styles.error}>{searchError}</Text> : null}

      {suggestions.length > 0 ? (
        <View style={styles.suggestions}>
          {suggestions.map((suggestion) => (
            <Pressable
              key={`${suggestion.lat}:${suggestion.lng}:${suggestion.address}`}
              style={styles.suggestionBtn}
              onPress={() => {
                setSuggestions([]);
                setQuery(suggestion.address);
                setCenter({ lat: suggestion.lat, lng: suggestion.lng });
                applyLocation(suggestion.lat, suggestion.lng, suggestion.address);
              }}
              accessibilityRole="button"
            >
              <Text numberOfLines={2} style={styles.suggestionLabel}>
                {suggestion.address}
              </Text>
            </Pressable>
          ))}
        </View>
      ) : null}

      <View style={styles.mapWrap}>
        <View style={styles.mapToolbar}>
          <Text style={styles.mapHint}>Tap or drag on the map to place your home pin.</Text>
          <View style={styles.zoomRow}>
            <Pressable style={styles.zoomBtn} onPress={() => setZoom((current) => clamp(current - 1, 10, 16))}>
              <Text style={styles.zoomLabel}>-</Text>
            </Pressable>
            <Text style={styles.zoomValue}>z{zoom}</Text>
            <Pressable style={styles.zoomBtn} onPress={() => setZoom((current) => clamp(current + 1, 10, 16))}>
              <Text style={styles.zoomLabel}>+</Text>
            </Pressable>
          </View>
        </View>

        <View
          style={styles.map}
          onLayout={onMapLayout}
          onStartShouldSetResponder={() => true}
          onMoveShouldSetResponder={() => true}
          onResponderGrant={(event) => {
            updateFromMapPoint(event.nativeEvent.locationX, event.nativeEvent.locationY);
          }}
          onResponderMove={(event) => {
            updateFromMapPoint(event.nativeEvent.locationX, event.nativeEvent.locationY);
          }}
        >
          <Image source={{ uri: mapUrl }} style={styles.mapImage} resizeMode="cover" />

          <View style={[styles.pinWrap, { left: pinPosition.x - 11, top: pinPosition.y - 30 }]} pointerEvents="none">
            <View style={styles.pinDot} />
            <View style={styles.pinStem} />
          </View>
        </View>

        <View style={styles.coordinateRow}>
          <Text style={styles.coordinateLabel}>Lat {marker.lat.toFixed(5)}</Text>
          <Text style={styles.coordinateLabel}>Lng {marker.lng.toFixed(5)}</Text>
        </View>

        <Text style={styles.addressLabel}>{value.address}</Text>

        <Pressable
          style={buttonStyles.secondaryBtn}
          onPress={() => {
            setCenter(SG_CENTER);
            setQuery("Singapore");
            setSuggestions([]);
            applyLocation(SG_CENTER.lat, SG_CENTER.lng, "Singapore");
          }}
          accessibilityRole="button"
        >
          <Text style={buttonStyles.secondaryLabel}>Reset To Singapore Center</Text>
        </Pressable>
      </View>

      {error ? <Text style={styles.error}>{error}</Text> : hint ? <Text style={styles.hint}>{hint}</Text> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: {
    gap: 10
  },
  label: {
    ...textStyles.label
  },
  searchRow: {
    flexDirection: "row",
    gap: 10
  },
  searchInput: {
    flex: 1,
    minHeight: 46,
    borderWidth: 1,
    borderColor: palette.border,
    borderRadius: 12,
    backgroundColor: palette.surface,
    paddingHorizontal: 14,
    color: palette.textPrimary,
    fontFamily: typography.body
  },
  searchBtn: {
    ...buttonStyles.primaryBtn,
    minWidth: 88
  },
  searchLabel: {
    ...buttonStyles.primaryLabel
  },
  suggestions: {
    gap: 8
  },
  suggestionBtn: {
    borderWidth: 1,
    borderColor: palette.border,
    borderRadius: 12,
    backgroundColor: palette.surface,
    paddingHorizontal: 12,
    paddingVertical: 10
  },
  suggestionLabel: {
    color: palette.textPrimary,
    fontFamily: typography.body,
    lineHeight: 18
  },
  mapWrap: {
    borderWidth: 1,
    borderColor: palette.border,
    borderRadius: 16,
    backgroundColor: palette.surface,
    padding: 10,
    gap: 10
  },
  mapToolbar: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    gap: 10
  },
  mapHint: {
    ...textStyles.helper,
    flex: 1
  },
  zoomRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6
  },
  zoomBtn: {
    width: 32,
    minHeight: 32,
    borderRadius: 999,
    borderWidth: 1,
    borderColor: palette.borderStrong,
    backgroundColor: palette.surface,
    alignItems: "center",
    justifyContent: "center"
  },
  zoomLabel: {
    color: palette.textPrimary,
    fontFamily: typography.body,
    fontSize: 18,
    lineHeight: 18,
    fontWeight: "700"
  },
  zoomValue: {
    color: palette.textSecondary,
    fontFamily: typography.body,
    fontWeight: "700"
  },
  map: {
    height: 240,
    borderRadius: 14,
    overflow: "hidden",
    borderWidth: 1,
    borderColor: palette.border
  },
  mapImage: {
    ...StyleSheet.absoluteFillObject
  },
  pinWrap: {
    position: "absolute",
    width: 22,
    height: 34,
    alignItems: "center"
  },
  pinDot: {
    width: 22,
    height: 22,
    borderRadius: 999,
    borderWidth: 2,
    borderColor: "#FFFFFF",
    backgroundColor: palette.accent,
    shadowColor: "#000000",
    shadowOpacity: 0.2,
    shadowOffset: { width: 0, height: 2 },
    shadowRadius: 4,
    elevation: 2
  },
  pinStem: {
    width: 2,
    height: 12,
    backgroundColor: palette.accent
  },
  coordinateRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8
  },
  coordinateLabel: {
    ...buttonStyles.subtleChipLabel
  },
  addressLabel: {
    ...textStyles.body
  },
  hint: {
    ...textStyles.helper
  },
  error: {
    color: palette.danger,
    fontFamily: typography.body,
    fontSize: 12
  }
});
