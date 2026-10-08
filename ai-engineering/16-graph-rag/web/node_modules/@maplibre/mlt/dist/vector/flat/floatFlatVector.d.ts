import { FixedSizeVector } from "../fixedSizeVector";
export declare class FloatFlatVector extends FixedSizeVector<Float32Array, number> {
    protected getValueFromBuffer(index: number): number;
}
