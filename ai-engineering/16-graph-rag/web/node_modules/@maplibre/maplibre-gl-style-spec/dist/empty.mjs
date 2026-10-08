import { latest } from "./reference/latest.mjs";
//#region src/empty.ts
function emptyStyle() {
	const style = {};
	const version = latest["$version"];
	for (const styleKey in latest["$root"]) {
		const specification = latest["$root"][styleKey];
		if (specification.required) {
			let value = null;
			if (styleKey === "version") value = version;
			else if (specification.type === "array") value = [];
			else value = {};
			if (value != null) style[styleKey] = value;
		}
	}
	return style;
}
//#endregion
export { emptyStyle };

//# sourceMappingURL=empty.mjs.map