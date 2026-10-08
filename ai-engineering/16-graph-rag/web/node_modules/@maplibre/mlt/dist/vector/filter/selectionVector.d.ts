export interface SelectionVector {
    getIndex(index: number): number;
    setIndex(index: number, value: number): void;
    setLimit(limit: number): void;
    selectionValues(): number[];
    get limit(): any;
    get capacity(): any;
}
