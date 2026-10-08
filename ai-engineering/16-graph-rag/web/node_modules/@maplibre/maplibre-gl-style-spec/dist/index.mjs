import { latest } from "./reference/latest.mjs";
import { derefLayers } from "./deref.mjs";
import { diff } from "./diff.mjs";
import { ValidationError } from "./error/validation_error.mjs";
import { ParsingError } from "./error/parsing_error.mjs";
import { ColorType, FormattedType, NullType, ProjectionDefinitionType, typeToString } from "./expression/types.mjs";
import { Color } from "./expression/types/color.mjs";
import { Formatted, FormattedSection } from "./expression/types/formatted.mjs";
import { Padding } from "./expression/types/padding.mjs";
import { NumberArray } from "./expression/types/number_array.mjs";
import { ColorArray } from "./expression/types/color_array.mjs";
import { VariableAnchorOffsetCollection } from "./expression/types/variable_anchor_offset_collection.mjs";
import { ResolvedImage } from "./expression/types/resolved_image.mjs";
import { ProjectionDefinition } from "./expression/types/projection_definition.mjs";
import { typeOf } from "./expression/values.mjs";
import { Literal } from "./expression/definitions/literal.mjs";
import { EvaluationContext } from "./expression/evaluation_context.mjs";
import { Step } from "./expression/definitions/step.mjs";
import { Interpolate, interpolateFactory } from "./expression/definitions/interpolate.mjs";
import { FormatExpression } from "./expression/definitions/format.mjs";
import { classifyRings } from "./util/classify_rings.mjs";
import { expressions } from "./expression/definitions/index.mjs";
import { CompoundExpression } from "./expression/compound_expression.mjs";
import { supportsPropertyExpression } from "./util/properties.mjs";
import { createFunction, isFunction } from "./function/index.mjs";
import { StyleExpression, StylePropertyFunction, ZoomConstantExpression, ZoomDependentExpression, createExpression, createPropertyExpression, isExpression, isZoomExpression, normalizePropertyExpression } from "./expression/index.mjs";
import { featureFilter, isExpressionFilter } from "./feature_filter/index.mjs";
import { convertFilter } from "./feature_filter/convert.mjs";
import { convertFunction } from "./function/convert.mjs";
import { eachLayer, eachProperty, eachSource } from "./visit.mjs";
import { groupByLayout } from "./group_by_layout.mjs";
import { emptyStyle } from "./empty.mjs";
import { validate } from "./validate/validate.mjs";
import { validateStyleMin } from "./validate_style.min.mjs";
import { format } from "./format.mjs";
import { migrate } from "./migrate.mjs";
import createVisibility from "./expression/visibility.mjs";
//#region src/index.ts
const expression = {
	StyleExpression,
	StylePropertyFunction,
	ZoomConstantExpression,
	ZoomDependentExpression,
	createExpression,
	createPropertyExpression,
	isExpression,
	isExpressionFilter,
	isZoomExpression,
	normalizePropertyExpression
};
const styleFunction = {
	convertFunction,
	createFunction,
	isFunction
};
const visit = {
	eachLayer,
	eachProperty,
	eachSource
};
//#endregion
export { Color, ColorArray, ColorType, CompoundExpression, EvaluationContext, FormatExpression, Formatted, FormattedSection, FormattedType, Interpolate, Literal, NullType, NumberArray, Padding, ParsingError, ProjectionDefinition, ProjectionDefinitionType, ResolvedImage, Step, StyleExpression, StylePropertyFunction, ValidationError, VariableAnchorOffsetCollection, ZoomConstantExpression, ZoomDependentExpression, classifyRings, convertFilter, convertFunction, createExpression, createFunction, createPropertyExpression, createVisibility as createVisibilityExpression, derefLayers, diff, emptyStyle, expression, expressions, featureFilter, format, styleFunction as function, groupByLayout, interpolateFactory as interpolates, isExpression, isFunction, isZoomExpression, latest, latest as v8, migrate, normalizePropertyExpression, supportsPropertyExpression, typeToString as toString, typeOf, validate, validateStyleMin, visit };

//# sourceMappingURL=index.mjs.map