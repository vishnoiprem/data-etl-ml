import type { SelectionVector } from "./selectionVector";
/**
 * Memory-efficient SelectionVector for arithmetic sequences (base + index * delta).
 * Calculates values on-demand, only materializes when modified.
 */
export declare class SequenceSelectionVector implements SelectionVector {
    private readonly _baseValue;
    private readonly _delta;
    private _limit;
    private readonly _capacity;
    private _materializedArray;
    constructor(_baseValue: number, _delta: number, _limit: number, _capacity?: number);
    /** @inheritdoc */
    get limit(): number;
    /** @inheritdoc */
    get capacity(): number;
    /** @inheritdoc */
    selectionValues(): number[];
    private materialize;
    /** @inheritdoc */
    getIndex(index: number): number;
    /** @inheritdoc */
    setIndex(index: number, value: number): void;
    /** @inheritdoc */
    setLimit(limit: number): void;
}
