export default class BitVector {
    private readonly values;
    private readonly _size;
    /**
     * @param values The byte buffer containing the bit values in least-significant bit (LSB)
     *     numbering
     */
    constructor(values: Uint8Array, size: number);
    get(index: number): boolean;
    set(index: number, value: boolean): void;
    getInt(index: number): number;
    size(): number;
    getBuffer(): Uint8Array;
}
