import type { StreamMetadata } from "../metadata/tile/streamMetadataDecoder";
import type BitVector from "../vector/flat/bitVector";
import type GeometryScaling from "../decoding/geometryScaling";
export declare function encodeSignedInt32Stream(values: Int32Array, metadata: StreamMetadata, bitVector?: BitVector, scalingData?: GeometryScaling): Uint8Array;
export declare function encodeUnsignedInt32Stream(values: Uint32Array, metadata: StreamMetadata, bitVector?: BitVector, scalingData?: GeometryScaling): Uint8Array;
export declare function encodeFloat64(values: Float64Array, streamMetadata: StreamMetadata, isSigned: boolean): Float64Array;
/**
 * Encodes BigInt64 values with zigzag encoding and varint compression
 */
export declare function encodeInt64SignedNone(values: BigInt64Array): Uint8Array;
/**
 * Encodes BigInt64 values with delta encoding, zigzag, and varint
 */
export declare function encodeInt64SignedDelta(values: BigInt64Array): Uint8Array;
/**
 * Encodes BigInt64 values with RLE, zigzag, and varint
 * @param runs - Array of [runLength, value] pairs
 */
export declare function encodeInt64SignedRle(runs: Array<[number, bigint]>): Uint8Array;
/**
 * Encodes BigInt64 values with delta+RLE, zigzag, and varint
 * @param runs - Array of [runLength, deltaValue] pairs representing RLE-encoded delta values
 */
export declare function encodeInt64SignedDeltaRle(runs: Array<[number, bigint]>): Uint8Array;
/**
 * Encodes unsigned BigInt64 values with varint compression (no zigzag)
 */
export declare function encodeInt64UnsignedNone(values: BigInt64Array): Uint8Array;
