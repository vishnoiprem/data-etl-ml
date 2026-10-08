export default class Vector {
    constructor(_name, dataBuffer, sizeOrNullabilityBuffer) {
        this._name = _name;
        this.dataBuffer = dataBuffer;
        if (typeof sizeOrNullabilityBuffer === "number") {
            this._size = sizeOrNullabilityBuffer;
        }
        else {
            this.nullabilityBuffer = sizeOrNullabilityBuffer;
            this._size = sizeOrNullabilityBuffer.size();
        }
    }
    getValue(index) {
        return this.nullabilityBuffer && !this.nullabilityBuffer.get(index) ? null : this.getValueFromBuffer(index);
    }
    has(index) {
        return this.nullabilityBuffer?.get(index) || !this.nullabilityBuffer;
    }
    get name() {
        return this._name;
    }
    get size() {
        return this._size;
    }
}
//# sourceMappingURL=vector.js.map