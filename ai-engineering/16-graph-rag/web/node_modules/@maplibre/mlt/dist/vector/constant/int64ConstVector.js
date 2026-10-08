import Vector from "../vector";
export class Int64ConstVector extends Vector {
    constructor(name, value, sizeOrNullabilityBuffer, isSigned) {
        super(name, isSigned ? BigInt64Array.of(value) : BigUint64Array.of(value), sizeOrNullabilityBuffer);
    }
    getValueFromBuffer(_index) {
        return this.dataBuffer[0];
    }
}
//# sourceMappingURL=int64ConstVector.js.map