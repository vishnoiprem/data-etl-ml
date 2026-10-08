/**
 * Decode FSST compressed data
 *
 * @param symbols           Array of symbols, where each symbol can be between 1 and 8 bytes
 * @param symbolLengths     Array of symbol lengths, length of each symbol in symbols array
 * @param compressedData    FSST Compressed data, where each entry is an index to the symbols array
 * @returns                 Decoded data as Uint8Array
 */
export declare function decodeFsst(symbols: Uint8Array, symbolLengths: Uint32Array, compressedData: Uint8Array): Uint8Array;
