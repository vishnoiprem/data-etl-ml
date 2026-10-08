import type IntWrapper from "../../decoding/intWrapper";
import type { Field, TileSetMetadata } from "./tilesetMetadata";
/**
 * Decodes a Field used as part of complex types (STRUCT children).
 */
export declare function decodeField(src: Uint8Array, offset: IntWrapper): Field;
/**
 * Top-level decoder for embedded tileset metadata.
 * Reads exactly ONE FeatureTableSchema from the stream.
 *
 * @param bytes The byte array containing the metadata
 * @param offset The current offset in the byte array (will be advanced)
 */
export declare function decodeEmbeddedTileSetMetadata(bytes: Uint8Array, offset: IntWrapper): [TileSetMetadata, number];
