import { ValidationError } from "../error/validation_error.mjs";
import { supportsPropertyExpression, transitionPropertyRegExp } from "../util/properties.mjs";
import { getType } from "../util/get_type.mjs";
import { isFunction } from "../function/index.mjs";
import { deepUnbundle, unbundle } from "../util/unbundle_jsonlint.mjs";
//#region src/validate/validate_property.ts
function validateProperty(options, propertyType) {
	const key = options.key;
	const validateSpec = options.validateSpec;
	const style = options.style;
	const styleSpec = options.styleSpec;
	const value = options.value;
	const propertyKey = options.objectKey;
	const layerSpec = styleSpec[`${propertyType}_${options.layerType}`];
	if (!layerSpec) return [];
	const transitionMatch = propertyKey.match(transitionPropertyRegExp);
	if (propertyType === "paint" && transitionMatch && layerSpec[transitionMatch[1]] && layerSpec[transitionMatch[1]].transition) return validateSpec({
		key,
		value,
		valueSpec: styleSpec.transition,
		style,
		styleSpec
	});
	const valueSpec = options.valueSpec || layerSpec[propertyKey];
	if (!valueSpec) return [new ValidationError(key, value, `unknown property "${propertyKey}"`)];
	let tokenMatch;
	if (getType(value) === "string" && supportsPropertyExpression(valueSpec) && !valueSpec.tokens && (tokenMatch = /^{([^}]+)}$/.exec(value))) return [new ValidationError(key, value, `"${propertyKey}" does not support interpolation syntax\nUse an identity property function instead: \`{ "type": "identity", "property": ${JSON.stringify(tokenMatch[1])} }\`.`)];
	const errors = [];
	if (options.layerType === "symbol") {
		if (propertyKey === "text-font" && isFunction(deepUnbundle(value)) && unbundle(value.type) === "identity") errors.push(new ValidationError(key, value, "\"text-font\" does not support identity functions"));
	}
	return errors.concat(validateSpec({
		key: options.key,
		value,
		valueSpec,
		style,
		styleSpec,
		expressionContext: "property",
		propertyType,
		propertyKey
	}));
}
//#endregion
export { validateProperty };

//# sourceMappingURL=validate_property.mjs.map