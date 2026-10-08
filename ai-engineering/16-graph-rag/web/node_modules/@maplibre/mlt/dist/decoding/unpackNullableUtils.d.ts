import BitVector from "../vector/flat/bitVector.js";
/**
 * Type constraint for TypedArray types that can be unpacked
 */
export type TypedArrayConstructor = Int32ArrayConstructor | Uint32ArrayConstructor | BigInt64ArrayConstructor | BigUint64ArrayConstructor | Float32ArrayConstructor | Float64ArrayConstructor;
export type TypedArrayInstance = Int32Array | Uint32Array | BigInt64Array | BigUint64Array | Float32Array | Float64Array;
/**
 * Generic unpacking function.
 * Reconstructs the full array by inserting default values at null positions.
 *
 * @param dataStream The compact data stream containing only non-null values
 * @param presentBits BitVector indicating which positions have values (null if non-nullable)
 * @param defaultValue The default value to insert at null positions (0, 0n, etc.)
 * @returns Full array with default values at null positions
 */
export declare function unpackNullable<T extends TypedArrayInstance>(dataStream: T, presentBits: BitVector | null, defaultValue: number | bigint): T;
/**
 * Special case for boolean columns because BitVector is not directly compatible with TypedArray.
 *
 * @param dataStream The compact BitVector data containing only non-null boolean values
 * @param dataStreamSize The number of actual values in dataStream
 * @param presentBits BitVector indicating which positions have values (null if non-nullable)
 * @returns Uint8Array buffer for BitVector with false at null positions
 */
export declare function unpackNullableBoolean(dataStream: Uint8Array, dataStreamSize: number, presentBits: BitVector | null): Uint8Array;
