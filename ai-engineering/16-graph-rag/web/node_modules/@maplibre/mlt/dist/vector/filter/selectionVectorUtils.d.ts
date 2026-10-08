import type { SelectionVector } from "./selectionVector";
import type BitVector from "../flat/bitVector";
import { SequenceSelectionVector } from "./sequenceSelectionVector";
export declare function createSelectionVector(size: number): SequenceSelectionVector;
/**
 * Creates a selection vector containing indices of non-null values.
 * @param size - The total number of elements to consider
 * @param nullabilityBuffer - Optional bit vector where 1=not null, 0=null. If undefined/null, all values are considered non-null.
 */
export declare function createNullableSelectionVector(size: number, nullabilityBuffer?: BitVector): SelectionVector;
/**
 * Filters an existing selection vector to include only non-null values.
 * @param selectionVector - The input selection vector to filter
 * @param nullabilityBuffer - Optional bit vector where 1=not null, 0=null. If undefined/null, all values are considered non-null.
 */
export declare function updateNullableSelectionVector(selectionVector: SelectionVector, nullabilityBuffer?: BitVector): SelectionVector;
