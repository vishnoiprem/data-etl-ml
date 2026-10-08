import type IntWrapper from "./intWrapper";
import type { Column } from "../metadata/tileset/tilesetMetadata";
import type Vector from "../vector/vector";
/**
 * Decodes a nested property (MAP) column into one vector per child column.
 *
 * The column is stored as a length stream (values per feature), a dictionary stream per value type
 * present, an optional presence stream, and a data stream of dictionary indices interleaved with
 * the control tokens that describe the map/list structure.
 *
 * Ported from the Java reference implementation (`MapPropertyDecoder`).
 */
export declare function decodeMapPropertyColumn(data: Uint8Array, offset: IntWrapper, columnMetadata: Column, numStreams: number): Vector[];
