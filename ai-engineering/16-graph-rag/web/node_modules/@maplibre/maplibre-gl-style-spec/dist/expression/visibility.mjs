import { createExpression, findGlobalStateRefs } from "./index.mjs";
//#region src/expression/visibility.ts
const visibilitySpec = {
	type: "enum",
	"property-type": "data-constant",
	expression: {
		interpolated: false,
		parameters: ["global-state"]
	},
	values: {
		visible: {},
		none: {}
	},
	transition: false,
	default: "visible"
};
var VisibilityExpressionClass = class {
	constructor(visibility, rootKey, globalState) {
		this._rootKey = rootKey;
		this._globalState = globalState;
		this.setValue(visibility);
	}
	evaluate() {
		return this._literalValue ?? this._compiledValue.evaluate({});
	}
	setValue(visibility) {
		if (visibility === null || visibility === void 0 || visibility === "visible" || visibility === "none") {
			this._literalValue = visibility === "none" ? "none" : "visible";
			this._compiledValue = void 0;
			this._globalStateRefs = /* @__PURE__ */ new Set();
			return;
		}
		const compiled = createExpression(visibility, this._rootKey, visibilitySpec, this._globalState);
		if (compiled.result === "error") {
			this._literalValue = "visible";
			this._compiledValue = void 0;
			throw new Error(compiled.value.map((err) => `${err.key}: ${err.message}`).join(", "));
		}
		this._literalValue = void 0;
		this._compiledValue = compiled.value;
		this._globalStateRefs = findGlobalStateRefs(compiled.value.expression);
	}
	getGlobalStateRefs() {
		return this._globalStateRefs;
	}
};
/**
* Creates a visibility expression from a visibility specification.
* @param visibility - the visibility specification, literal or expression
* @param rootKey - location of the visibility value in the style JSON
* (e.g. `layers[3].layout.visibility`), used to prefix runtime warnings
* @param globalState - the global state object
* @returns visibility expression object
*/
function createVisibility(visibility, rootKey, globalState) {
	return new VisibilityExpressionClass(visibility, rootKey, globalState);
}
//#endregion
export { createVisibility as default };

//# sourceMappingURL=visibility.mjs.map