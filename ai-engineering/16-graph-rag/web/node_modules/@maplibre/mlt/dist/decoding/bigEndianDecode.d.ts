/**
 * Decodes big-endian bytes into `out` without allocating the output buffer.
 *
 * This function does not copy `bytes`; it writes decoded words into the provided `out` array.
 * For aligned inputs it may create a temporary typed-array view (`Uint32Array`) over `bytes.buffer`
 * to speed up decoding.
 *
 * If `byteLength` is not a multiple of 4, the final word is padded with zeros.
 *
 * @returns Number of int32 words written.
 * @throws RangeError If `(offset, byteLength)` is out of bounds, or if `out` is too small.
 */
export declare function decodeBigEndianInt32sInto(bytes: Uint8Array, offset: number, byteLength: number, out: Uint32Array): number;
