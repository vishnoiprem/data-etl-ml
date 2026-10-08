import FeatureTable from "./vector/featureTable";
import type GeometryScaling from "./decoding/geometryScaling";
/**
 * Decodes a tile with embedded metadata (Tag 0x01 format).
 * This is the primary decoder function for MLT tiles.
 *
 * @param tile The tile data to decode (will be decompressed if gzip-compressed)
 * @param geometryScaling Optional geometry scaling parameters
 * @param idWithinMaxSafeInteger If true, limits ID values to JavaScript safe integer range (53 bits)
 */
export default function decodeTile(tile: Uint8Array, geometryScaling?: GeometryScaling, idWithinMaxSafeInteger?: boolean): FeatureTable[];
