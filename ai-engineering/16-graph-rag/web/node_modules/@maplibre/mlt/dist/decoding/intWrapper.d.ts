export default class IntWrapper {
    private value;
    constructor(value: number);
    get(): number;
    set(v: number): void;
    increment(): number;
    add(v: number): void;
}
