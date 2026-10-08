/**
 * Encodes plain strings into a complete stream with PRESENT (if needed), LENGTH, and DATA streams.
 * @param strings - Array of strings (can include null values)
 * @returns Encoded Uint8Array that can be passed to decodeString
 */
export declare function encodePlainStrings(strings: (string | null)[]): Uint8Array;
/**
 * Encodes dictionary-compressed strings into a complete stream.
 * @param strings - Array of strings (can include null values)
 * @returns Encoded Uint8Array that can be passed to decodeString
 */
export declare function encodeDictionaryStrings(strings: (string | null)[]): Uint8Array;
