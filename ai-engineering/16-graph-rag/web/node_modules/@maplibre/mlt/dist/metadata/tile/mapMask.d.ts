/**
 * Bitmask written ahead of a nested property (MAP) column, marking which optional streams follow
 * the mandatory length stream. Only one of INT32/INT64 and one of UINT32/UINT64 is ever set: the
 * encoder picks the narrower width that fits every value.
 */
export declare enum MapMask {
    STRING = 1,
    INT32 = 2,
    UINT32 = 4,
    INT64 = 8,
    UINT64 = 16,
    FLOAT = 32,
    DOUBLE = 64,
    PRESENCE = 128
}
