// Ported from https://github.com/lemire/JavaFastPFOR/blob/master/src/main/java/me/lemire/integercompression/IntWrapper.java
export default class IntWrapper {
    constructor(value) {
        this.value = value;
    }
    get() {
        return this.value;
    }
    set(v) {
        this.value = v;
    }
    increment() {
        return this.value++;
    }
    add(v) {
        this.value += v;
    }
}
//# sourceMappingURL=intWrapper.js.map