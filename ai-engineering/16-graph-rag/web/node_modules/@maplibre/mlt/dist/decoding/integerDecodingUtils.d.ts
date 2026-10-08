import type IntWrapper from "./intWrapper";
import { type FastPforWireDecodeWorkspace } from "./fastPforDecoder";
export type { FastPforWireDecodeWorkspace } from "./fastPforDecoder";
export { createFastPforWireDecodeWorkspace } from "./fastPforDecoder";
export declare function decodeVarintInt32(buf: Uint8Array, bufferOffset: IntWrapper, numValues: number): Uint32Array;
export declare function decodeVarintInt64(src: Uint8Array, offset: IntWrapper, numValues: number): BigUint64Array;
export declare function decodeVarintFloat64(src: Uint8Array, offset: IntWrapper, numValues: number): Float64Array;
export declare function decodeFastPfor(encodedBytes: Uint8Array, expectedValueCount: number, encodedByteLength: number, offset: IntWrapper): Uint32Array;
export declare function decodeFastPforWithWorkspace(encodedBytes: Uint8Array, expectedValueCount: number, encodedByteLength: number, offset: IntWrapper, workspace: FastPforWireDecodeWorkspace): Uint32Array;
export declare function decodeZigZagInt32Value(encoded: number): number;
export declare function decodeZigZagInt64Value(encoded: bigint): bigint;
export declare function decodeZigZagFloat64Value(encoded: number): number;
export declare function decodeZigZagInt32(encodedData: Uint32Array): Int32Array;
export declare function decodeZigZagInt64(encodedData: BigUint64Array): BigInt64Array;
export declare function decodeZigZagFloat64(encodedData: Float64Array): void;
export declare function decodeUnsignedRleInt32(encodedData: Uint32Array, numRuns: number, numTotalValues?: number): Uint32Array;
export declare function decodeUnsignedRleInt64(encodedData: BigUint64Array, numRuns: number, numTotalValues?: number): BigUint64Array;
export declare function decodeUnsignedRleFloat64(encodedData: Float64Array, numRuns: number, numTotalValues: number): Float64Array;
export declare function decodeZigZagDeltaInt32(data: Uint32Array): Int32Array;
export declare function decodeZigZagDeltaInt64(data: BigInt64Array | BigUint64Array): BigInt64Array;
export declare function decodeZigZagDeltaFloat64(data: Float64Array): void;
export declare function decodeZigZagRleInt32(data: Uint32Array, numRuns: number, numTotalValues?: number): Int32Array;
export declare function decodeZigZagRleInt64(data: BigUint64Array, numRuns: number, numTotalValues?: number): BigInt64Array;
export declare function decodeZigZagRleFloat64(data: Float64Array, numRuns: number, numTotalValues: number): Float64Array;
export declare function fastInverseDelta(data: Uint32Array | Int32Array): void;
export declare function inverseDelta(data: Uint32Array): void;
export declare function decodeComponentwiseDeltaVec2(data: Uint32Array): Int32Array;
export declare function decodeComponentwiseDeltaVec2Scaled(data: Uint32Array, scale: number, min: number, max: number): Int32Array;
export declare function decodeZigZagDeltaOfDeltaInt32(data: Uint32Array): Uint32Array;
export declare function decodeZigZagRleDeltaInt32(data: Uint32Array, numRuns: number, numTotalValues: number): Int32Array;
export declare function decodeRleDeltaInt32(data: Uint32Array, numRuns: number, numTotalValues: number): Uint32Array;
/**
 * Decode Delta-RLE with multiple runs by fully reconstructing values.
 *
 * @param data RLE encoded data: [run1, run2, ..., value1, value2, ...]
 * @param numRuns Number of runs in the RLE encoding
 * @param numValues Total number of values to reconstruct
 * @returns Reconstructed values with deltas applied
 */
export declare function decodeDeltaRleInt32(data: Uint32Array, numRuns: number, numValues: number): Int32Array;
/**
 * Decode Delta-RLE with multiple runs for 64-bit integers.
 */
export declare function decodeDeltaRleInt64(data: BigUint64Array, numRuns: number, numValues: number): BigInt64Array;
export declare function decodeUnsignedZigZagDeltaInt32(data: Uint32Array): Uint32Array;
export declare function decodeUnsignedZigZagDeltaInt64(data: BigUint64Array): BigUint64Array;
export declare function decodeUnsignedComponentwiseDeltaVec2(data: Uint32Array): Uint32Array;
export declare function decodeUnsignedComponentwiseDeltaVec2Scaled(data: Uint32Array, scale: number, min: number, max: number): Uint32Array;
export declare function decodeUnsignedConstRleInt32(data: Int32Array | Uint32Array): number;
export declare function decodeZigZagConstRleInt32(data: Int32Array | Uint32Array): number;
export declare function decodeZigZagSequenceRleInt32(data: Int32Array | Uint32Array): [baseValue: number, delta: number];
export declare function decodeUnsignedConstRleInt64(data: BigInt64Array | BigUint64Array): bigint;
export declare function decodeZigZagConstRleInt64(data: BigInt64Array | BigUint64Array): bigint;
export declare function decodeZigZagSequenceRleInt64(data: BigInt64Array | BigUint64Array): [baseValue: bigint, delta: bigint];
