import { PhysicalStreamType } from "../metadata/tile/physicalStreamType";
import { LogicalLevelTechnique } from "../metadata/tile/logicalLevelTechnique";
import { PhysicalLevelTechnique } from "../metadata/tile/physicalLevelTechnique";
import { DictionaryType } from "../metadata/tile/dictionaryType";
import { type Column } from "../metadata/tileset/tilesetMetadata";
import type { RleEncodedStreamMetadata, StreamMetadata } from "../metadata/tile/streamMetadataDecoder";
import type { LogicalStreamType } from "../metadata/tile/logicalStreamType";
/**
 * Creates basic stream metadata with logical techniques.
 */
export declare function createStreamMetadata(logicalTechnique1: LogicalLevelTechnique, logicalTechnique2?: LogicalLevelTechnique, numValues?: number): StreamMetadata;
/**
 * Creates RLE-encoded stream metadata.
 */
export declare function createRleMetadata(logicalTechnique1: LogicalLevelTechnique, logicalTechnique2: LogicalLevelTechnique, runs: number, numRleValues: number): RleEncodedStreamMetadata;
/**
 * Creates column metadata for STRUCT type columns.
 */
export declare function createColumnMetadataForStruct(columnName: string, childFields: Array<{
    name: string;
    type?: number;
    nullable?: boolean;
}>): Column;
/**
 * Creates a single stream with metadata and data.
 */
export declare function createStream(physicalType: PhysicalStreamType, data: Uint8Array, options?: {
    logical?: LogicalStreamType;
    technique?: PhysicalLevelTechnique;
    count?: number;
}): Uint8Array;
/**
 * Encodes FSST-compressed strings into a complete stream.
 * This uses hardcoded test data: ["cat", "dog", "cat"]
 * @returns Encoded Uint8Array that can be passed to decodeString
 */
export declare function encodeFsstStrings(): Uint8Array;
/**
 * Encodes a shared dictionary for struct fields.
 * @param dictionaryStrings - Array of unique strings in the dictionary
 * @param options - Encoding options
 * @returns Object containing length and data streams
 */
export declare function encodeSharedDictionary(dictionaryStrings: string[], options?: {
    useFsst?: boolean;
    dictionaryType?: DictionaryType;
}): {
    lengthStream: Uint8Array;
    dataStream: Uint8Array;
    symbolLengthStream?: Uint8Array;
    symbolDataStream?: Uint8Array;
};
/**
 * Encodes streams for a struct field.
 * @param offsetIndices - Indices into the shared dictionary
 * @param presentValues - Boolean array indicating which values are present
 * @param isPresent - Whether the field itself is present
 * @returns Encoded streams for the field
 */
export declare function encodeStructField(offsetIndices: number[], presentValues: boolean[], isPresent?: boolean): Uint8Array;
/**
 * Builds a complete encoded stream by combining metadata and data.
 */
export declare function buildEncodedStream(streamMetadata: StreamMetadata | RleEncodedStreamMetadata, encodedData: Uint8Array): Uint8Array;
/**
 * Encodes stream metadata into binary format.
 * - Byte 1: Stream type (physical type in upper 4 bits, logical subtype in lower 4 bits)
 * - Byte 2: Encodings (llt1[5-7], llt2[2-4], plt[0-1])
 * - Varints: numValues, byteLength
 * - If RLE: Varints: runs, numRleValues
 */
export declare function encodeStreamMetadata(metadata: StreamMetadata | RleEncodedStreamMetadata): Uint8Array;
/**
 * Concatenates multiple Uint8Array buffers into a single buffer.
 */
export declare function concatenateBuffers(...buffers: Uint8Array[]): Uint8Array;
