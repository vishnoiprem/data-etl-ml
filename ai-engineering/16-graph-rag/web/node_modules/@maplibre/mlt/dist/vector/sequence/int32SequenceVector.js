import { SequenceVector } from "./sequenceVector";
export class Int32SequenceVector extends SequenceVector {
    constructor(name, baseValue, delta, size, isSigned) {
        super(name, isSigned ? Int32Array.of(baseValue) : Uint32Array.of(baseValue), delta, size);
    }
    getValueFromBuffer(index) {
        return this.dataBuffer[0] + index * this.delta;
    }
}
//# sourceMappingURL=int32SequenceVector.js.map