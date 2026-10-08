//#region src/expression/types/formatted.ts
const VERTICAL_ALIGN_OPTIONS = [
	"bottom",
	"center",
	"top"
];
var FormattedSection = class {
	constructor(text, image, scale, fontStack, textColor, verticalAlign) {
		this.text = text;
		this.image = image;
		this.scale = scale;
		this.fontStack = fontStack;
		this.textColor = textColor;
		this.verticalAlign = verticalAlign;
	}
};
var Formatted = class Formatted {
	constructor(sections) {
		this.sections = sections;
	}
	static fromString(unformatted) {
		return new Formatted([new FormattedSection(unformatted, null, null, null, null, null)]);
	}
	isEmpty() {
		if (this.sections.length === 0) return true;
		return !this.sections.some((section) => section.text.length !== 0 || section.image && section.image.name.length !== 0);
	}
	static factory(text) {
		if (text instanceof Formatted) return text;
		else return Formatted.fromString(text);
	}
	toString() {
		if (this.sections.length === 0) return "";
		return this.sections.map((section) => section.text).join("");
	}
};
//#endregion
export { Formatted, FormattedSection, VERTICAL_ALIGN_OPTIONS };

//# sourceMappingURL=formatted.mjs.map