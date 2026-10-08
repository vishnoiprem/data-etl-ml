/**
 * Array-based SelectionVector for non-sequential selections.
 * Stores indices explicitly, suitable for irregular patterns and frequent modifications.
 */
export class FlatSelectionVector {
    /**
     * @param _selectionVector
     * @param _limit In write mode the limit of a Buffer is the limit of how much data you can write into the buffer.
     * In write mode the limit is equal to the capacity of the Buffer.
     */
    constructor(_selectionVector, _limit) {
        this._selectionVector = _selectionVector;
        this._limit = _limit;
        if (!this._limit) {
            this._limit = this._selectionVector.length;
        }
    }
    /** @inheritdoc */
    getIndex(index) {
        if (index >= this._limit || index < 0) {
            throw new RangeError("Index out of bounds");
        }
        return this._selectionVector[index];
    }
    /** @inheritdoc */
    setIndex(index, value) {
        if (index >= this._limit || index < 0) {
            throw new RangeError("Index out of bounds");
        }
        this._selectionVector[index] = value;
    }
    /** @inheritdoc */
    setLimit(limit) {
        if (limit < 0 || limit > this.capacity) {
            throw new RangeError("Limit out of bounds");
        }
        this._limit = limit;
    }
    /** @inheritdoc */
    selectionValues() {
        return this._selectionVector;
    }
    /** @inheritdoc */
    get capacity() {
        return this._selectionVector.length;
    }
    /** @inheritdoc */
    get limit() {
        return this._limit;
    }
}
//# sourceMappingURL=flatSelectionVector.js.map