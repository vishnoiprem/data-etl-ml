import Vector from "../vector";
export class Int32ConstVector extends Vector {
    constructor(name, value, sizeOrNullabilityBuffer, isSigned) {
        super(name, isSigned ? Int32Array.of(value) : Uint32Array.of(value), sizeOrNullabilityBuffer);
    }
    getValueFromBuffer(_index) {
        return this.dataBuffer[0];
    }
}
//# sourceMappingURL=int32ConstVector.js.map