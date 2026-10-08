export declare const MASKS: Readonly<Uint32Array>;
export declare const DEFAULT_PAGE_SIZE = 65536;
export declare const BLOCK_SIZE = 256;
export declare function greatestMultiple(value: number, factor: number): number;
export declare function roundUpToMultipleOf32(value: number): number;
export declare function normalizePageSize(pageSize: number): number;
export declare function bswap32(value: number): number;
