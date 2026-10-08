import Vector from "../vector";
export class SequenceVector extends Vector {
    constructor(name, baseValueBuffer, delta, size) {
        super(name, baseValueBuffer, size);
        this.delta = delta;
    }
}
//# sourceMappingURL=sequenceVector.js.map