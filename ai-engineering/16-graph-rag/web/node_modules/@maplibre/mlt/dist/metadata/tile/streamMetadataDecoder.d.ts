import { LogicalLevelTechnique } from "./logicalLevelTechnique";
import { PhysicalLevelTechnique } from "./physicalLevelTechnique";
import { PhysicalStreamType } from "./physicalStreamType";
import type { LogicalStreamType } from "./logicalStreamType";
import type IntWrapper from "../../decoding/intWrapper";
export type StreamMetadata = {
    readonly physicalStreamType: PhysicalStreamType;
    readonly logicalStreamType: LogicalStreamType;
    readonly logicalLevelTechnique1: LogicalLevelTechnique;
    readonly logicalLevelTechnique2: LogicalLevelTechnique;
    readonly physicalLevelTechnique: PhysicalLevelTechnique;
    readonly numValues: number;
    readonly byteLength: number;
    /**
     * Returns the number of decompressed values.
     * For non-RLE streams, this is the same as numValues.
     * For RLE streams, this is overridden to return numRleValues.
     */
    readonly decompressedCount: number;
};
export type MortonEncodedStreamMetadata = StreamMetadata & {
    readonly numBits: number;
    readonly coordinateShift: number;
};
export type RleEncodedStreamMetadata = StreamMetadata & {
    readonly runs: number;
    readonly numRleValues: number;
};
export declare function decodeStreamMetadata(tile: Uint8Array, offset: IntWrapper): StreamMetadata;
