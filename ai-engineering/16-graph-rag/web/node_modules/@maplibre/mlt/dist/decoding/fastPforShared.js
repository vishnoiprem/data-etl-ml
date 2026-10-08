/**
 * Bit masks for each bitwidth 0-32.
 * DO NOT MUTATE - this is a shared constant.
 */
const masks = new Uint32Array(33);
masks[0] = 0;
for (let bitWidth = 1; bitWidth <= 32; bitWidth++) {
    masks[bitWidth] = bitWidth === 32 ? 0xffffffff : 0xffffffff >>> (32 - bitWidth);
}
export const MASKS = masks;
export const DEFAULT_PAGE_SIZE = 65536;
export const BLOCK_SIZE = 256;
export function greatestMultiple(value, factor) {
    return value - (value % factor);
}
export function roundUpToMultipleOf32(value) {
    return greatestMultiple(value + 31, 32);
}
export function normalizePageSize(pageSize) {
    if (!Number.isFinite(pageSize) || pageSize <= 0)
        return DEFAULT_PAGE_SIZE;
    const aligned = greatestMultiple(Math.floor(pageSize), BLOCK_SIZE);
    return aligned === 0 ? BLOCK_SIZE : aligned;
}
export function bswap32(value) {
    const x = value >>> 0;
    return (((x & 0xff) << 24) | ((x & 0xff00) << 8) | ((x >>> 8) & 0xff00) | ((x >>> 24) & 0xff)) >>> 0;
}
//# sourceMappingURL=fastPforShared.js.map