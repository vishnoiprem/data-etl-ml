/**
 * Memory-efficient SelectionVector for arithmetic sequences (base + index * delta).
 * Calculates values on-demand, only materializes when modified.
 */
export class SequenceSelectionVector {
    constructor(_baseValue, _delta, _limit, _capacity = _limit) {
        this._baseValue = _baseValue;
        this._delta = _delta;
        this._limit = _limit;
        this._capacity = _capacity;
        this._materializedArray = null;
    }
    /** @inheritdoc */
    get limit() {
        return this._limit;
    }
    /** @inheritdoc */
    get capacity() {
        return this._capacity;
    }
    /** @inheritdoc */
    selectionValues() {
        if (!this._materializedArray) {
            this._materializedArray = this.materialize();
        }
        return this._materializedArray;
    }
    materialize() {
        const arr = new Array(this._capacity);
        for (let i = 0; i < this._capacity; i++) {
            arr[i] = this._baseValue + i * this._delta;
        }
        return arr;
    }
    /** @inheritdoc */
    getIndex(index) {
        if (index >= this._limit || index < 0) {
            throw new RangeError("Index out of bounds");
        }
        if (this._materializedArray) {
            return this._materializedArray[index];
        }
        return this._baseValue + index * this._delta;
    }
    /** @inheritdoc */
    setIndex(index, value) {
        if (index >= this._limit || index < 0) {
            throw new RangeError("Index out of bounds");
        }
        if (!this._materializedArray) {
            this._materializedArray = this.materialize();
        }
        this._materializedArray[index] = value;
    }
    /** @inheritdoc */
    setLimit(limit) {
        if (limit < 0 || limit > this.capacity) {
            throw new RangeError("Limit out of bounds");
        }
        this._limit = limit;
    }
}
//# sourceMappingURL=sequenceSelectionVector.js.map