/**
 * Create symbol table from string array
 *
 * @param symbolStrings     Array of symbol strings
 * @returns                 Symbol table buffer and lengths
 */
export declare function createSymbolTable(symbolStrings: string[]): {
    symbols: Uint8Array;
    symbolLengths: Uint32Array;
};
/**
 * Encode data using FSST compression with pre-defined symbol table
 * Encoder requires pre-defined symbol table. Real FSST learns optimal symbols from data. This
 * implementation is for testing decoder only.
 *
 * @param symbols           Array of symbols, where each symbol can be between 1 and 8 bytes
 * @param symbolLengths     Array of symbol lengths, length of each symbol in symbols array
 * @param uncompressedData  Data to compress
 * @returns                 FSST compressed data, where each entry is an index to the symbols array
 */
export declare function encodeFsst(symbols: Uint8Array, symbolLengths: Uint32Array, uncompressedData: Uint8Array): Uint8Array;
