import type { SelectionVector } from "./selectionVector";
/**
 * Array-based SelectionVector for non-sequential selections.
 * Stores indices explicitly, suitable for irregular patterns and frequent modifications.
 */
export declare class FlatSelectionVector implements SelectionVector {
    private _selectionVector;
    private _limit?;
    /**
     * @param _selectionVector
     * @param _limit In write mode the limit of a Buffer is the limit of how much data you can write into the buffer.
     * In write mode the limit is equal to the capacity of the Buffer.
     */
    constructor(_selectionVector: number[], _limit?: number);
    /** @inheritdoc */
    getIndex(index: number): number;
    /** @inheritdoc */
    setIndex(index: number, value: number): void;
    /** @inheritdoc */
    setLimit(limit: number): void;
    /** @inheritdoc */
    selectionValues(): number[];
    /** @inheritdoc */
    get capacity(): number;
    /** @inheritdoc */
    get limit(): number;
}
