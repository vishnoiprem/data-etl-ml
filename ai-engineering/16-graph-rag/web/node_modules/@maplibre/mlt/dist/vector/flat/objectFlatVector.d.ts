import Vector from "../vector";
import type BitVector from "./bitVector";
/**
 * Holds already-decoded values of arbitrary shape, one per feature.
 *
 * Unlike the other vectors there is no packed buffer to index into: nested property (MAP) columns
 * decode to plain JavaScript maps, arrays and scalars, so the values are kept as-is. Features
 * without a value are marked absent in the nullability buffer, so `has` reports them as missing and
 * `getValue` returns `null`.
 */
export declare class ObjectFlatVector extends Vector<Uint8Array, unknown> {
    private readonly values;
    constructor(name: string, values: unknown[], nullabilityBuffer?: BitVector);
    protected getValueFromBuffer(index: number): unknown;
}
