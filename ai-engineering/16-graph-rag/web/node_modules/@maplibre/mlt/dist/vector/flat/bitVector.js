export default class BitVector {
    /**
     * @param values The byte buffer containing the bit values in least-significant bit (LSB)
     *     numbering
     */
    constructor(values, size) {
        this.values = values;
        this._size = size;
    }
    get(index) {
        const byteIndex = Math.floor(index / 8);
        const bitIndex = index % 8;
        const b = this.values[byteIndex];
        return ((b >> bitIndex) & 1) === 1;
    }
    set(index, value) {
        //TODO: refactor -> improve quick and dirty solution
        const byteIndex = Math.floor(index / 8);
        const bitIndex = index % 8;
        this.values[byteIndex] = this.values[byteIndex] | ((value ? 1 : 0) << bitIndex);
    }
    getInt(index) {
        const byteIndex = Math.floor(index / 8);
        const bitIndex = index % 8;
        const b = this.values[byteIndex];
        return (b >> bitIndex) & 1;
    }
    size() {
        return this._size;
    }
    getBuffer() {
        return this.values;
    }
}
//# sourceMappingURL=bitVector.js.map