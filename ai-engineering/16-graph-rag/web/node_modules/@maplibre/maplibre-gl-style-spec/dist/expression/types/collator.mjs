//#region src/expression/types/collator.ts
var Collator = class {
	constructor(caseSensitive, diacriticSensitive, locale) {
		if (caseSensitive) this.sensitivity = diacriticSensitive ? "variant" : "case";
		else this.sensitivity = diacriticSensitive ? "accent" : "base";
		this.locale = locale;
		this.collator = new Intl.Collator(this.locale ? this.locale : [], {
			sensitivity: this.sensitivity,
			usage: "search"
		});
	}
	compare(lhs, rhs) {
		return this.collator.compare(lhs, rhs);
	}
	resolvedLocale() {
		return new Intl.Collator(this.locale ? this.locale : []).resolvedOptions().locale;
	}
};
//#endregion
export { Collator };

//# sourceMappingURL=collator.mjs.map