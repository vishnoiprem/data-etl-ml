/**
 * Serializes an `Int32Array` to a big-endian byte stream.
 *
 * @param values - Int32 words to serialize.
 * @returns Big-endian byte stream (`values.length * 4` bytes).
 */
export declare function encodeBigEndianInt32s(values: Uint32Array): Uint8Array;
