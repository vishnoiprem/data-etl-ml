import Vector from "../vector";
export class BooleanFlatVector extends Vector {
    constructor(name, dataVector, sizeOrNullabilityBuffer) {
        super(name, dataVector.getBuffer(), sizeOrNullabilityBuffer);
        this.dataVector = dataVector;
    }
    getValueFromBuffer(index) {
        return this.dataVector.get(index);
    }
}
//# sourceMappingURL=booleanFlatVector.js.map