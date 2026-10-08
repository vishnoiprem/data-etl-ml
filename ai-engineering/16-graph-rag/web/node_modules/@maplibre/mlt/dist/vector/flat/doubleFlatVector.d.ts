import { FixedSizeVector } from "../fixedSizeVector";
export declare class DoubleFlatVector extends FixedSizeVector<Float64Array, number> {
    protected getValueFromBuffer(index: number): number;
}
