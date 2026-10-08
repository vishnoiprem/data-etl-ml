//#region src/expression/types/projection_definition.ts
var ProjectionDefinition = class ProjectionDefinition {
	constructor(from, to, transition) {
		this.from = from;
		this.to = to;
		this.transition = transition;
	}
	toString() {
		if (this.from === this.to && this.transition === 1) return this.from;
		return JSON.stringify([
			this.from,
			this.to,
			this.transition
		]);
	}
	static interpolate(from, to, t) {
		return new ProjectionDefinition(from, to, t);
	}
	static parse(input) {
		if (input instanceof ProjectionDefinition) return input;
		if (Array.isArray(input) && input.length === 3 && typeof input[0] === "string" && typeof input[1] === "string" && typeof input[2] === "number") return new ProjectionDefinition(input[0], input[1], input[2]);
		if (typeof input === "object" && typeof input.from === "string" && typeof input.to === "string" && typeof input.transition === "number") return new ProjectionDefinition(input.from, input.to, input.transition);
		if (typeof input === "string") return new ProjectionDefinition(input, input, 1);
	}
};
//#endregion
export { ProjectionDefinition };

//# sourceMappingURL=projection_definition.mjs.map