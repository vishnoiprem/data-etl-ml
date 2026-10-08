#!/usr/bin/env node
//#region \0rolldown/runtime.js
var __create = Object.create;
var __defProp = Object.defineProperty;
var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
var __getOwnPropNames = Object.getOwnPropertyNames;
var __getProtoOf = Object.getPrototypeOf;
var __hasOwnProp = Object.prototype.hasOwnProperty;
var __commonJSMin = (cb, mod) => () => (mod || (cb((mod = { exports: {} }).exports, mod), cb = null), mod.exports);
var __copyProps = (to, from, except, desc) => {
	if (from && typeof from === "object" || typeof from === "function") for (var keys = __getOwnPropNames(from), i = 0, n = keys.length, key; i < n; i++) {
		key = keys[i];
		if (!__hasOwnProp.call(to, key) && key !== except) __defProp(to, key, {
			get: ((k) => from[k]).bind(null, key),
			enumerable: !(desc = __getOwnPropDesc(from, key)) || desc.enumerable
		});
	}
	return to;
};
var __toESM = (mod, isNodeMode, target) => (target = mod != null ? __create(__getProtoOf(mod)) : {}, __copyProps(isNodeMode || !mod || !mod.__esModule || !__hasOwnProp.call(mod, "default") ? __defProp(target, "default", {
	value: mod,
	enumerable: true
}) : target, mod));
//#endregion
let fs = require("fs");
fs = __toESM(fs, 1);
//#endregion
//#region src/reference/v8.json
var import_minimist = /* @__PURE__ */ __toESM((/* @__PURE__ */ __commonJSMin(((exports, module) => {
	function hasKey(obj, keys) {
		var o = obj;
		keys.slice(0, -1).forEach(function(key) {
			o = o[key] || {};
		});
		return keys[keys.length - 1] in o;
	}
	function isNumber(x) {
		if (typeof x === "number") return true;
		if (/^0x[0-9a-f]+$/i.test(x)) return true;
		return /^[-+]?(?:\d+(?:\.\d*)?|\.\d+)(e[-+]?\d+)?$/.test(x);
	}
	function isConstructorOrProto(obj, key) {
		return key === "constructor" && typeof obj[key] === "function" || key === "__proto__";
	}
	module.exports = function(args, opts) {
		if (!opts) opts = {};
		var flags = {
			bools: {},
			strings: {},
			unknownFn: null
		};
		if (typeof opts.unknown === "function") flags.unknownFn = opts.unknown;
		if (typeof opts.boolean === "boolean" && opts.boolean) flags.allBools = true;
		else [].concat(opts.boolean).filter(Boolean).forEach(function(key) {
			flags.bools[key] = true;
		});
		var aliases = {};
		function aliasIsBoolean(key) {
			return aliases[key].some(function(x) {
				return flags.bools[x];
			});
		}
		Object.keys(opts.alias || {}).forEach(function(key) {
			aliases[key] = [].concat(opts.alias[key]);
			aliases[key].forEach(function(x) {
				aliases[x] = [key].concat(aliases[key].filter(function(y) {
					return x !== y;
				}));
			});
		});
		[].concat(opts.string).filter(Boolean).forEach(function(key) {
			flags.strings[key] = true;
			if (aliases[key]) [].concat(aliases[key]).forEach(function(k) {
				flags.strings[k] = true;
			});
		});
		var defaults = opts.default || {};
		var argv = { _: [] };
		function argDefined(key, arg) {
			return flags.allBools && /^--[^=]+$/.test(arg) || flags.strings[key] || flags.bools[key] || aliases[key];
		}
		function setKey(obj, keys, value) {
			var o = obj;
			for (var i = 0; i < keys.length - 1; i++) {
				var key = keys[i];
				if (isConstructorOrProto(o, key)) return;
				if (o[key] === void 0) o[key] = {};
				if (o[key] === Object.prototype || o[key] === Number.prototype || o[key] === String.prototype) o[key] = {};
				if (o[key] === Array.prototype) o[key] = [];
				o = o[key];
			}
			var lastKey = keys[keys.length - 1];
			if (isConstructorOrProto(o, lastKey)) return;
			if (o === Object.prototype || o === Number.prototype || o === String.prototype) o = {};
			if (o === Array.prototype) o = [];
			if (o[lastKey] === void 0 || flags.bools[lastKey] || typeof o[lastKey] === "boolean") o[lastKey] = value;
			else if (Array.isArray(o[lastKey])) o[lastKey].push(value);
			else o[lastKey] = [o[lastKey], value];
		}
		function setArg(key, val, arg) {
			if (arg && flags.unknownFn && !argDefined(key, arg)) {
				if (flags.unknownFn(arg) === false) return;
			}
			var value = !flags.strings[key] && isNumber(val) ? Number(val) : val;
			setKey(argv, key.split("."), value);
			(aliases[key] || []).forEach(function(x) {
				setKey(argv, x.split("."), value);
			});
		}
		Object.keys(flags.bools).forEach(function(key) {
			setArg(key, defaults[key] === void 0 ? false : defaults[key]);
		});
		var notFlags = [];
		if (args.indexOf("--") !== -1) {
			notFlags = args.slice(args.indexOf("--") + 1);
			args = args.slice(0, args.indexOf("--"));
		}
		for (var i = 0; i < args.length; i++) {
			var arg = args[i];
			var key;
			var next;
			if (/^--.+=/.test(arg)) {
				var m = arg.match(/^--([^=]+)=([\s\S]*)$/);
				key = m[1];
				var value = m[2];
				if (flags.bools[key]) value = value !== "false";
				setArg(key, value, arg);
			} else if (/^--no-.+/.test(arg)) {
				key = arg.match(/^--no-(.+)/)[1];
				setArg(key, false, arg);
			} else if (/^--.+/.test(arg)) {
				key = arg.match(/^--(.+)/)[1];
				next = args[i + 1];
				if (next !== void 0 && !/^(-|--)[^-]/.test(next) && !flags.bools[key] && !flags.allBools && (aliases[key] ? !aliasIsBoolean(key) : true)) {
					setArg(key, next, arg);
					i += 1;
				} else if (/^(true|false)$/.test(next)) {
					setArg(key, next === "true", arg);
					i += 1;
				} else setArg(key, flags.strings[key] ? "" : true, arg);
			} else if (/^-[^-]+/.test(arg)) {
				var letters = arg.slice(1, -1).split("");
				var broken = false;
				for (var j = 0; j < letters.length; j++) {
					next = arg.slice(j + 2);
					if (next === "-") {
						setArg(letters[j], next, arg);
						continue;
					}
					if (/[A-Za-z]/.test(letters[j]) && next[0] === "=") {
						setArg(letters[j], next.slice(1), arg);
						broken = true;
						break;
					}
					if (/[A-Za-z]/.test(letters[j]) && /-?\d+(\.\d*)?(e-?\d+)?$/.test(next)) {
						setArg(letters[j], next, arg);
						broken = true;
						break;
					}
					if (letters[j + 1] && letters[j + 1].match(/\W/)) {
						setArg(letters[j], arg.slice(j + 2), arg);
						broken = true;
						break;
					} else setArg(letters[j], flags.strings[letters[j]] ? "" : true, arg);
				}
				key = arg.slice(-1)[0];
				if (!broken && key !== "-") {
					if (args[i + 1] && !/^(-|--)[^-]/.test(args[i + 1]) && !flags.bools[key] && (aliases[key] ? !aliasIsBoolean(key) : true)) {
						setArg(key, args[i + 1], arg);
						i += 1;
					} else if (args[i + 1] && /^(true|false)$/.test(args[i + 1])) {
						setArg(key, args[i + 1] === "true", arg);
						i += 1;
					} else setArg(key, flags.strings[key] ? "" : true, arg);
				}
			} else {
				if (!flags.unknownFn || flags.unknownFn(arg) !== false) argv._.push(flags.strings._ || !isNumber(arg) ? arg : Number(arg));
				if (opts.stopEarly) {
					argv._.push.apply(argv._, args.slice(i + 1));
					break;
				}
			}
		}
		Object.keys(defaults).forEach(function(k) {
			if (!hasKey(argv, k.split("."))) {
				setKey(argv, k.split("."), defaults[k]);
				(aliases[k] || []).forEach(function(x) {
					setKey(argv, x.split("."), defaults[k]);
				});
			}
		});
		if (opts["--"]) argv["--"] = notFlags.slice();
		else notFlags.forEach(function(k) {
			argv._.push(k);
		});
		return argv;
	};
})))(), 1);
var v8_default = {
	$version: 8,
	$root: {
		"version": {
			"required": true,
			"type": "enum",
			"values": [8]
		},
		"name": { "type": "string" },
		"metadata": { "type": "*" },
		"center": {
			"type": "array",
			"value": "number",
			"length": 2
		},
		"centerAltitude": { "type": "number" },
		"zoom": { "type": "number" },
		"bearing": {
			"type": "number",
			"default": 0,
			"period": 360,
			"units": "degrees"
		},
		"pitch": {
			"type": "number",
			"default": 0,
			"units": "degrees"
		},
		"roll": {
			"type": "number",
			"default": 0,
			"units": "degrees"
		},
		"state": {
			"type": "state",
			"default": {}
		},
		"light": { "type": "light" },
		"sky": { "type": "sky" },
		"projection": { "type": "projection" },
		"terrain": { "type": "terrain" },
		"sources": {
			"required": true,
			"type": "sources"
		},
		"sprite": { "type": "sprite" },
		"glyphs": { "type": "string" },
		"font-faces": { "type": "fontFaces" },
		"transition": { "type": "transition" },
		"layers": {
			"required": true,
			"type": "array",
			"value": "layer"
		}
	},
	sources: { "*": { "type": "source" } },
	source: [
		"source_vector",
		"source_raster",
		"source_raster_dem",
		"source_geojson",
		"source_video",
		"source_image"
	],
	source_vector: {
		"type": {
			"required": true,
			"type": "enum",
			"values": { "vector": {} }
		},
		"url": { "type": "string" },
		"tiles": {
			"type": "array",
			"value": "string"
		},
		"bounds": {
			"type": "array",
			"value": "number",
			"length": 4,
			"default": [
				-180,
				-85.051129,
				180,
				85.051129
			]
		},
		"scheme": {
			"type": "enum",
			"values": {
				"xyz": {},
				"tms": {}
			},
			"default": "xyz"
		},
		"minzoom": {
			"type": "number",
			"default": 0
		},
		"maxzoom": {
			"type": "number",
			"default": 22
		},
		"attribution": { "type": "string" },
		"promoteId": { "type": "promoteId" },
		"volatile": {
			"type": "boolean",
			"default": false
		},
		"encoding": {
			"type": "enum",
			"values": {
				"mvt": {},
				"mlt": {}
			},
			"default": "mvt"
		},
		"*": { "type": "*" }
	},
	source_raster: {
		"type": {
			"required": true,
			"type": "enum",
			"values": { "raster": {} }
		},
		"url": { "type": "string" },
		"tiles": {
			"type": "array",
			"value": "string"
		},
		"bounds": {
			"type": "array",
			"value": "number",
			"length": 4,
			"default": [
				-180,
				-85.051129,
				180,
				85.051129
			]
		},
		"minzoom": {
			"type": "number",
			"default": 0
		},
		"maxzoom": {
			"type": "number",
			"default": 22
		},
		"tileSize": {
			"type": "number",
			"default": 512,
			"units": "pixels"
		},
		"scheme": {
			"type": "enum",
			"values": {
				"xyz": {},
				"tms": {}
			},
			"default": "xyz"
		},
		"attribution": { "type": "string" },
		"volatile": {
			"type": "boolean",
			"default": false
		},
		"*": { "type": "*" }
	},
	source_raster_dem: {
		"type": {
			"required": true,
			"type": "enum",
			"values": { "raster-dem": {} }
		},
		"url": { "type": "string" },
		"tiles": {
			"type": "array",
			"value": "string"
		},
		"bounds": {
			"type": "array",
			"value": "number",
			"length": 4,
			"default": [
				-180,
				-85.051129,
				180,
				85.051129
			]
		},
		"minzoom": {
			"type": "number",
			"default": 0
		},
		"maxzoom": {
			"type": "number",
			"default": 22
		},
		"tileSize": {
			"type": "number",
			"default": 512,
			"units": "pixels"
		},
		"attribution": { "type": "string" },
		"encoding": {
			"type": "enum",
			"values": {
				"terrarium": {},
				"mapbox": {},
				"custom": {}
			},
			"default": "mapbox"
		},
		"redFactor": {
			"type": "number",
			"default": 1
		},
		"blueFactor": {
			"type": "number",
			"default": 1
		},
		"greenFactor": {
			"type": "number",
			"default": 1
		},
		"baseShift": {
			"type": "number",
			"default": 0
		},
		"volatile": {
			"type": "boolean",
			"default": false
		},
		"*": { "type": "*" }
	},
	source_geojson: {
		"type": {
			"required": true,
			"type": "enum",
			"values": { "geojson": {} }
		},
		"data": {
			"required": true,
			"type": "*"
		},
		"maxzoom": {
			"type": "number",
			"default": 18
		},
		"attribution": { "type": "string" },
		"buffer": {
			"type": "number",
			"default": 128,
			"maximum": 512,
			"minimum": 0
		},
		"filter": { "type": "filter" },
		"tolerance": {
			"type": "number",
			"default": .375
		},
		"cluster": {
			"type": "boolean",
			"default": false
		},
		"clusterRadius": {
			"type": "number",
			"default": 50,
			"minimum": 0
		},
		"clusterMaxZoom": { "type": "number" },
		"clusterMinPoints": { "type": "number" },
		"clusterProperties": { "type": "*" },
		"lineMetrics": {
			"type": "boolean",
			"default": false
		},
		"generateId": {
			"type": "boolean",
			"default": false
		},
		"promoteId": { "type": "promoteId" }
	},
	source_video: {
		"type": {
			"required": true,
			"type": "enum",
			"values": { "video": {} }
		},
		"urls": {
			"required": true,
			"type": "array",
			"value": "string"
		},
		"coordinates": {
			"required": true,
			"type": "array",
			"length": 4,
			"value": {
				"type": "array",
				"length": 2,
				"value": "number"
			}
		}
	},
	source_image: {
		"type": {
			"required": true,
			"type": "enum",
			"values": { "image": {} }
		},
		"url": { "type": "string" },
		"coordinates": {
			"required": true,
			"type": "array",
			"length": 4,
			"value": {
				"type": "array",
				"length": 2,
				"value": "number"
			}
		}
	},
	layer: {
		"id": {
			"type": "string",
			"required": true
		},
		"type": {
			"type": "enum",
			"values": {
				"fill": {},
				"line": {},
				"symbol": {},
				"circle": {},
				"heatmap": {},
				"fill-extrusion": {},
				"raster": {},
				"hillshade": {},
				"color-relief": {},
				"background": {}
			},
			"required": true
		},
		"metadata": { "type": "*" },
		"source": { "type": "string" },
		"source-layer": { "type": "string" },
		"minzoom": {
			"type": "number",
			"minimum": 0,
			"maximum": 24
		},
		"maxzoom": {
			"type": "number",
			"minimum": 0,
			"maximum": 24
		},
		"filter": { "type": "filter" },
		"layout": { "type": "layout" },
		"paint": { "type": "paint" }
	},
	layout: [
		"layout_fill",
		"layout_line",
		"layout_circle",
		"layout_heatmap",
		"layout_fill-extrusion",
		"layout_symbol",
		"layout_raster",
		"layout_hillshade",
		"layout_color-relief",
		"layout_background"
	],
	layout_background: { "visibility": {
		"type": "enum",
		"values": {
			"visible": {},
			"none": {}
		},
		"default": "visible",
		"expression": {
			"interpolated": false,
			"parameters": ["global-state"]
		},
		"property-type": "data-constant"
	} },
	layout_fill: {
		"fill-sort-key": {
			"type": "number",
			"expression": {
				"interpolated": false,
				"parameters": ["zoom", "feature"]
			},
			"property-type": "data-driven"
		},
		"visibility": {
			"type": "enum",
			"values": {
				"visible": {},
				"none": {}
			},
			"default": "visible",
			"expression": {
				"interpolated": false,
				"parameters": ["global-state"]
			},
			"property-type": "data-constant"
		}
	},
	layout_circle: {
		"circle-sort-key": {
			"type": "number",
			"expression": {
				"interpolated": false,
				"parameters": ["zoom", "feature"]
			},
			"property-type": "data-driven"
		},
		"visibility": {
			"type": "enum",
			"values": {
				"visible": {},
				"none": {}
			},
			"default": "visible",
			"expression": {
				"interpolated": false,
				"parameters": ["global-state"]
			},
			"property-type": "data-constant"
		}
	},
	layout_heatmap: { "visibility": {
		"type": "enum",
		"values": {
			"visible": {},
			"none": {}
		},
		"default": "visible",
		"expression": {
			"interpolated": false,
			"parameters": ["global-state"]
		},
		"property-type": "data-constant"
	} },
	"layout_fill-extrusion": {
		"visibility": {
			"type": "enum",
			"values": {
				"visible": {},
				"none": {}
			},
			"default": "visible",
			"expression": {
				"interpolated": false,
				"parameters": ["global-state"]
			},
			"property-type": "data-constant"
		},
		"fill-extrusion-rounded-corner-distance": {
			"type": "number",
			"default": 0,
			"minimum": 0,
			"units": "meters",
			"property-type": "constant"
		}
	},
	layout_line: {
		"line-cap": {
			"type": "enum",
			"values": {
				"butt": {},
				"round": {},
				"square": {}
			},
			"default": "butt",
			"expression": {
				"interpolated": false,
				"parameters": ["zoom", "feature"]
			},
			"property-type": "data-driven"
		},
		"line-join": {
			"type": "enum",
			"values": {
				"bevel": {},
				"round": {},
				"miter": {}
			},
			"default": "miter",
			"expression": {
				"interpolated": false,
				"parameters": ["zoom", "feature"]
			},
			"property-type": "data-driven"
		},
		"line-miter-limit": {
			"type": "number",
			"default": 2,
			"requires": [{ "line-join": "miter" }],
			"expression": {
				"interpolated": true,
				"parameters": ["zoom", "feature"]
			},
			"property-type": "data-driven"
		},
		"line-round-limit": {
			"type": "number",
			"default": 1.05,
			"requires": [{ "line-join": "round" }],
			"expression": {
				"interpolated": true,
				"parameters": ["zoom", "feature"]
			},
			"property-type": "data-driven"
		},
		"line-sort-key": {
			"type": "number",
			"expression": {
				"interpolated": false,
				"parameters": ["zoom", "feature"]
			},
			"property-type": "data-driven"
		},
		"visibility": {
			"type": "enum",
			"values": {
				"visible": {},
				"none": {}
			},
			"default": "visible",
			"expression": {
				"interpolated": false,
				"parameters": ["global-state"]
			},
			"property-type": "data-constant"
		}
	},
	layout_symbol: {
		"symbol-placement": {
			"type": "enum",
			"values": {
				"point": {},
				"line": {},
				"line-center": {}
			},
			"default": "point",
			"expression": {
				"interpolated": false,
				"parameters": ["zoom"]
			},
			"property-type": "data-constant"
		},
		"symbol-spacing": {
			"type": "number",
			"default": 250,
			"minimum": 1,
			"units": "pixels",
			"requires": [{ "symbol-placement": "line" }],
			"expression": {
				"interpolated": true,
				"parameters": ["zoom"]
			},
			"property-type": "data-constant"
		},
		"symbol-avoid-edges": {
			"type": "boolean",
			"default": false,
			"expression": {
				"interpolated": false,
				"parameters": ["zoom"]
			},
			"property-type": "data-constant"
		},
		"symbol-sort-key": {
			"type": "number",
			"expression": {
				"interpolated": false,
				"parameters": ["zoom", "feature"]
			},
			"property-type": "data-driven"
		},
		"symbol-z-order": {
			"type": "enum",
			"values": {
				"auto": {},
				"viewport-y": {},
				"source": {}
			},
			"default": "auto",
			"expression": {
				"interpolated": false,
				"parameters": ["zoom"]
			},
			"property-type": "data-constant"
		},
		"icon-allow-overlap": {
			"type": "boolean",
			"default": false,
			"requires": ["icon-image", { "!": "icon-overlap" }],
			"expression": {
				"interpolated": false,
				"parameters": ["zoom"]
			},
			"property-type": "data-constant"
		},
		"icon-overlap": {
			"type": "enum",
			"values": {
				"never": {},
				"always": {},
				"cooperative": {}
			},
			"requires": ["icon-image"],
			"expression": {
				"interpolated": false,
				"parameters": ["zoom"]
			},
			"property-type": "data-constant"
		},
		"icon-ignore-placement": {
			"type": "boolean",
			"default": false,
			"requires": ["icon-image"],
			"expression": {
				"interpolated": false,
				"parameters": ["zoom"]
			},
			"property-type": "data-constant"
		},
		"icon-optional": {
			"type": "boolean",
			"default": false,
			"requires": ["icon-image", "text-field"],
			"expression": {
				"interpolated": false,
				"parameters": ["zoom"]
			},
			"property-type": "data-constant"
		},
		"icon-rotation-alignment": {
			"type": "enum",
			"values": {
				"map": {},
				"viewport": {},
				"auto": {}
			},
			"default": "auto",
			"requires": ["icon-image"],
			"expression": {
				"interpolated": false,
				"parameters": ["zoom", "feature"]
			},
			"property-type": "data-driven"
		},
		"icon-size": {
			"type": "number",
			"default": 1,
			"minimum": 0,
			"units": "factor of the original icon size",
			"requires": ["icon-image"],
			"expression": {
				"interpolated": true,
				"parameters": ["zoom", "feature"]
			},
			"property-type": "data-driven"
		},
		"icon-text-fit": {
			"type": "enum",
			"values": {
				"none": {},
				"width": {},
				"height": {},
				"both": {}
			},
			"default": "none",
			"requires": ["icon-image", "text-field"],
			"expression": {
				"interpolated": false,
				"parameters": ["zoom"]
			},
			"property-type": "data-constant"
		},
		"icon-text-fit-padding": {
			"type": "array",
			"value": "number",
			"length": 4,
			"default": [
				0,
				0,
				0,
				0
			],
			"units": "pixels",
			"requires": [
				"icon-image",
				"text-field",
				{ "icon-text-fit": [
					"both",
					"width",
					"height"
				] }
			],
			"expression": {
				"interpolated": true,
				"parameters": ["zoom"]
			},
			"property-type": "data-constant"
		},
		"icon-image": {
			"type": "resolvedImage",
			"tokens": true,
			"expression": {
				"interpolated": false,
				"parameters": ["zoom", "feature"]
			},
			"property-type": "data-driven"
		},
		"icon-rotate": {
			"type": "number",
			"default": 0,
			"period": 360,
			"units": "degrees",
			"requires": ["icon-image"],
			"expression": {
				"interpolated": true,
				"parameters": ["zoom", "feature"]
			},
			"property-type": "data-driven"
		},
		"icon-padding": {
			"type": "padding",
			"default": [2],
			"units": "pixels",
			"requires": ["icon-image"],
			"expression": {
				"interpolated": true,
				"parameters": ["zoom", "feature"]
			},
			"property-type": "data-driven"
		},
		"icon-keep-upright": {
			"type": "boolean",
			"default": false,
			"requires": [
				"icon-image",
				{ "icon-rotation-alignment": "map" },
				{ "symbol-placement": ["line", "line-center"] }
			],
			"expression": {
				"interpolated": false,
				"parameters": ["zoom"]
			},
			"property-type": "data-constant"
		},
		"icon-offset": {
			"type": "array",
			"value": "number",
			"length": 2,
			"default": [0, 0],
			"requires": ["icon-image"],
			"expression": {
				"interpolated": true,
				"parameters": ["zoom", "feature"]
			},
			"property-type": "data-driven"
		},
		"icon-anchor": {
			"type": "enum",
			"values": {
				"center": {},
				"left": {},
				"right": {},
				"top": {},
				"bottom": {},
				"top-left": {},
				"top-right": {},
				"bottom-left": {},
				"bottom-right": {}
			},
			"default": "center",
			"requires": ["icon-image"],
			"expression": {
				"interpolated": false,
				"parameters": ["zoom", "feature"]
			},
			"property-type": "data-driven"
		},
		"icon-pitch-alignment": {
			"type": "enum",
			"values": {
				"map": {},
				"viewport": {},
				"auto": {}
			},
			"default": "auto",
			"requires": ["icon-image"],
			"expression": {
				"interpolated": false,
				"parameters": ["zoom"]
			},
			"property-type": "data-constant"
		},
		"text-pitch-alignment": {
			"type": "enum",
			"values": {
				"map": {},
				"viewport": {},
				"auto": {}
			},
			"default": "auto",
			"requires": ["text-field"],
			"expression": {
				"interpolated": false,
				"parameters": ["zoom"]
			},
			"property-type": "data-constant"
		},
		"text-rotation-alignment": {
			"type": "enum",
			"values": {
				"map": {},
				"viewport": {},
				"viewport-glyph": {},
				"auto": {}
			},
			"default": "auto",
			"requires": ["text-field"],
			"expression": {
				"interpolated": false,
				"parameters": ["zoom"]
			},
			"property-type": "data-constant"
		},
		"text-field": {
			"type": "formatted",
			"default": "",
			"tokens": true,
			"expression": {
				"interpolated": false,
				"parameters": ["zoom", "feature"]
			},
			"property-type": "data-driven"
		},
		"text-font": {
			"type": "array",
			"value": "string",
			"default": ["Open Sans Regular", "Arial Unicode MS Regular"],
			"requires": ["text-field"],
			"expression": {
				"interpolated": false,
				"parameters": ["zoom", "feature"]
			},
			"property-type": "data-driven"
		},
		"text-size": {
			"type": "number",
			"default": 16,
			"minimum": 0,
			"units": "pixels",
			"requires": ["text-field"],
			"expression": {
				"interpolated": true,
				"parameters": ["zoom", "feature"]
			},
			"property-type": "data-driven"
		},
		"text-max-width": {
			"type": "number",
			"default": 10,
			"minimum": 0,
			"units": "ems",
			"requires": ["text-field"],
			"expression": {
				"interpolated": true,
				"parameters": ["zoom", "feature"]
			},
			"property-type": "data-driven"
		},
		"text-line-height": {
			"type": "number",
			"default": 1.2,
			"units": "ems",
			"requires": ["text-field"],
			"expression": {
				"interpolated": true,
				"parameters": ["zoom"]
			},
			"property-type": "data-constant"
		},
		"text-letter-spacing": {
			"type": "number",
			"default": 0,
			"units": "ems",
			"requires": ["text-field"],
			"expression": {
				"interpolated": true,
				"parameters": ["zoom", "feature"]
			},
			"property-type": "data-driven"
		},
		"text-justify": {
			"type": "enum",
			"values": {
				"auto": {},
				"left": {},
				"center": {},
				"right": {}
			},
			"default": "center",
			"requires": ["text-field"],
			"expression": {
				"interpolated": false,
				"parameters": ["zoom", "feature"]
			},
			"property-type": "data-driven"
		},
		"text-radial-offset": {
			"type": "number",
			"units": "ems",
			"default": 0,
			"requires": ["text-field"],
			"property-type": "data-driven",
			"expression": {
				"interpolated": true,
				"parameters": ["zoom", "feature"]
			}
		},
		"text-variable-anchor": {
			"type": "array",
			"value": "enum",
			"values": {
				"center": {},
				"left": {},
				"right": {},
				"top": {},
				"bottom": {},
				"top-left": {},
				"top-right": {},
				"bottom-left": {},
				"bottom-right": {}
			},
			"requires": ["text-field", { "symbol-placement": ["point"] }],
			"expression": {
				"interpolated": false,
				"parameters": ["zoom"]
			},
			"property-type": "data-constant"
		},
		"text-variable-anchor-offset": {
			"type": "variableAnchorOffsetCollection",
			"requires": ["text-field", { "symbol-placement": ["point"] }],
			"expression": {
				"interpolated": true,
				"parameters": ["zoom", "feature"]
			},
			"property-type": "data-driven"
		},
		"text-anchor": {
			"type": "enum",
			"values": {
				"center": {},
				"left": {},
				"right": {},
				"top": {},
				"bottom": {},
				"top-left": {},
				"top-right": {},
				"bottom-left": {},
				"bottom-right": {}
			},
			"default": "center",
			"requires": ["text-field", { "!": "text-variable-anchor" }],
			"expression": {
				"interpolated": false,
				"parameters": ["zoom", "feature"]
			},
			"property-type": "data-driven"
		},
		"text-max-angle": {
			"type": "number",
			"default": 45,
			"units": "degrees",
			"requires": ["text-field", { "symbol-placement": ["line", "line-center"] }],
			"expression": {
				"interpolated": true,
				"parameters": ["zoom"]
			},
			"property-type": "data-constant"
		},
		"text-writing-mode": {
			"type": "array",
			"value": "enum",
			"values": {
				"horizontal": {},
				"vertical": {}
			},
			"requires": ["text-field", { "symbol-placement": ["point"] }],
			"expression": {
				"interpolated": false,
				"parameters": ["zoom"]
			},
			"property-type": "data-constant"
		},
		"text-rotate": {
			"type": "number",
			"default": 0,
			"period": 360,
			"units": "degrees",
			"requires": ["text-field"],
			"expression": {
				"interpolated": true,
				"parameters": ["zoom", "feature"]
			},
			"property-type": "data-driven"
		},
		"text-padding": {
			"type": "number",
			"default": 2,
			"minimum": 0,
			"units": "pixels",
			"requires": ["text-field"],
			"expression": {
				"interpolated": true,
				"parameters": ["zoom"]
			},
			"property-type": "data-constant"
		},
		"text-keep-upright": {
			"type": "boolean",
			"default": true,
			"requires": [
				"text-field",
				{ "text-rotation-alignment": "map" },
				{ "symbol-placement": ["line", "line-center"] }
			],
			"expression": {
				"interpolated": false,
				"parameters": ["zoom"]
			},
			"property-type": "data-constant"
		},
		"text-transform": {
			"type": "enum",
			"values": {
				"none": {},
				"uppercase": {},
				"lowercase": {}
			},
			"default": "none",
			"requires": ["text-field"],
			"expression": {
				"interpolated": false,
				"parameters": ["zoom", "feature"]
			},
			"property-type": "data-driven"
		},
		"text-offset": {
			"type": "array",
			"value": "number",
			"units": "ems",
			"length": 2,
			"default": [0, 0],
			"requires": ["text-field", { "!": "text-radial-offset" }],
			"expression": {
				"interpolated": true,
				"parameters": ["zoom", "feature"]
			},
			"property-type": "data-driven"
		},
		"text-allow-overlap": {
			"type": "boolean",
			"default": false,
			"requires": ["text-field", { "!": "text-overlap" }],
			"expression": {
				"interpolated": false,
				"parameters": ["zoom"]
			},
			"property-type": "data-constant"
		},
		"text-overlap": {
			"type": "enum",
			"values": {
				"never": {},
				"always": {},
				"cooperative": {}
			},
			"requires": ["text-field"],
			"expression": {
				"interpolated": false,
				"parameters": ["zoom"]
			},
			"property-type": "data-constant"
		},
		"text-ignore-placement": {
			"type": "boolean",
			"default": false,
			"requires": ["text-field"],
			"expression": {
				"interpolated": false,
				"parameters": ["zoom"]
			},
			"property-type": "data-constant"
		},
		"text-optional": {
			"type": "boolean",
			"default": false,
			"requires": ["text-field", "icon-image"],
			"expression": {
				"interpolated": false,
				"parameters": ["zoom"]
			},
			"property-type": "data-constant"
		},
		"symbol-height-offset": {
			"type": "number",
			"default": 0,
			"units": "meters",
			"requires": [{ "symbol-placement": ["point"] }],
			"expression": {
				"interpolated": true,
				"parameters": ["zoom", "feature"]
			},
			"property-type": "data-driven"
		},
		"symbol-height-anchor": {
			"type": "enum",
			"values": {
				"ground": {},
				"absolute": {}
			},
			"default": "ground",
			"requires": ["symbol-height-offset"],
			"expression": {
				"interpolated": false,
				"parameters": ["zoom"]
			},
			"property-type": "data-constant"
		},
		"visibility": {
			"type": "enum",
			"values": {
				"visible": {},
				"none": {}
			},
			"default": "visible",
			"expression": {
				"interpolated": false,
				"parameters": ["global-state"]
			},
			"property-type": "data-constant"
		}
	},
	layout_raster: { "visibility": {
		"type": "enum",
		"values": {
			"visible": {},
			"none": {}
		},
		"default": "visible",
		"expression": {
			"interpolated": false,
			"parameters": ["global-state"]
		},
		"property-type": "data-constant"
	} },
	layout_hillshade: { "visibility": {
		"type": "enum",
		"values": {
			"visible": {},
			"none": {}
		},
		"default": "visible",
		"expression": {
			"interpolated": false,
			"parameters": ["global-state"]
		},
		"property-type": "data-constant"
	} },
	"layout_color-relief": { "visibility": {
		"type": "enum",
		"values": {
			"visible": {},
			"none": {}
		},
		"default": "visible",
		"expression": {
			"interpolated": false,
			"parameters": ["global-state"]
		},
		"property-type": "data-constant"
	} },
	filter: {
		"type": "boolean",
		"expression": {
			"interpolated": false,
			"parameters": ["zoom", "feature"]
		},
		"property-type": "data-driven"
	},
	filter_operator: {
		"type": "enum",
		"values": {
			"==": {},
			"!=": {},
			">": {},
			">=": {},
			"<": {},
			"<=": {},
			"in": {},
			"!in": {},
			"all": {},
			"any": {},
			"none": {},
			"has": {},
			"!has": {}
		}
	},
	geometry_type: {
		"type": "enum",
		"values": {
			"Point": {},
			"LineString": {},
			"Polygon": {}
		}
	},
	"function": {
		"expression": { "type": "expression" },
		"stops": {
			"type": "array",
			"value": "function_stop"
		},
		"base": {
			"type": "number",
			"default": 1,
			"minimum": 0
		},
		"property": {
			"type": "string",
			"default": "$zoom"
		},
		"type": {
			"type": "enum",
			"values": {
				"identity": {},
				"exponential": {},
				"interval": {},
				"categorical": {}
			},
			"default": "exponential"
		},
		"colorSpace": {
			"type": "enum",
			"values": {
				"rgb": {},
				"lab": {},
				"hcl": {}
			},
			"default": "rgb"
		},
		"default": {
			"type": "*",
			"required": false
		}
	},
	function_stop: {
		"type": "array",
		"minimum": 0,
		"maximum": 24,
		"value": ["number", "color"],
		"length": 2
	},
	expression: {
		"type": "array",
		"value": "expression_name",
		"minimum": 1
	},
	light: {
		"anchor": {
			"type": "enum",
			"default": "viewport",
			"values": {
				"map": {},
				"viewport": {}
			},
			"property-type": "data-constant",
			"transition": false,
			"expression": {
				"interpolated": false,
				"parameters": ["zoom"]
			}
		},
		"position": {
			"type": "array",
			"default": [
				1.15,
				210,
				30
			],
			"length": 3,
			"value": "number",
			"property-type": "data-constant",
			"transition": true,
			"expression": {
				"interpolated": true,
				"parameters": ["zoom"]
			}
		},
		"color": {
			"type": "color",
			"property-type": "data-constant",
			"default": "#ffffff",
			"expression": {
				"interpolated": true,
				"parameters": ["zoom"]
			},
			"transition": true
		},
		"intensity": {
			"type": "number",
			"property-type": "data-constant",
			"default": .5,
			"minimum": 0,
			"maximum": 1,
			"expression": {
				"interpolated": true,
				"parameters": ["zoom"]
			},
			"transition": true
		}
	},
	sky: {
		"sky-color": {
			"type": "color",
			"property-type": "data-constant",
			"default": "#88C6FC",
			"expression": {
				"interpolated": true,
				"parameters": ["zoom"]
			},
			"transition": true
		},
		"horizon-color": {
			"type": "color",
			"property-type": "data-constant",
			"default": "#ffffff",
			"expression": {
				"interpolated": true,
				"parameters": ["zoom"]
			},
			"transition": true
		},
		"fog-color": {
			"type": "color",
			"property-type": "data-constant",
			"default": "#ffffff",
			"expression": {
				"interpolated": true,
				"parameters": ["zoom"]
			},
			"transition": true
		},
		"fog-ground-blend": {
			"type": "number",
			"property-type": "data-constant",
			"default": .5,
			"minimum": 0,
			"maximum": 1,
			"expression": {
				"interpolated": true,
				"parameters": ["zoom"]
			},
			"transition": true
		},
		"horizon-fog-blend": {
			"type": "number",
			"property-type": "data-constant",
			"default": .8,
			"minimum": 0,
			"maximum": 1,
			"expression": {
				"interpolated": true,
				"parameters": ["zoom"]
			},
			"transition": true
		},
		"sky-horizon-blend": {
			"type": "number",
			"property-type": "data-constant",
			"default": .8,
			"minimum": 0,
			"maximum": 1,
			"expression": {
				"interpolated": true,
				"parameters": ["zoom"]
			},
			"transition": true
		},
		"atmosphere-blend": {
			"type": "number",
			"property-type": "data-constant",
			"default": .8,
			"minimum": 0,
			"maximum": 1,
			"expression": {
				"interpolated": true,
				"parameters": ["zoom"]
			},
			"transition": true
		}
	},
	terrain: {
		"source": {
			"type": "string",
			"required": true
		},
		"exaggeration": {
			"type": "number",
			"minimum": 0,
			"default": 1
		}
	},
	projection: { "type": {
		"type": "projectionDefinition",
		"default": "mercator",
		"property-type": "data-constant",
		"transition": false,
		"expression": {
			"interpolated": true,
			"parameters": ["zoom"]
		}
	} },
	paint: [
		"paint_fill",
		"paint_line",
		"paint_circle",
		"paint_heatmap",
		"paint_fill-extrusion",
		"paint_symbol",
		"paint_raster",
		"paint_hillshade",
		"paint_color-relief",
		"paint_background"
	],
	paint_fill: {
		"fill-antialias": {
			"type": "boolean",
			"default": true,
			"expression": {
				"interpolated": false,
				"parameters": ["zoom"]
			},
			"property-type": "data-constant"
		},
		"fill-opacity": {
			"type": "number",
			"default": 1,
			"minimum": 0,
			"maximum": 1,
			"transition": true,
			"expression": {
				"interpolated": true,
				"parameters": [
					"zoom",
					"feature",
					"feature-state"
				]
			},
			"property-type": "data-driven"
		},
		"fill-layer-opacity": {
			"type": "number",
			"default": 1,
			"minimum": 0,
			"maximum": 1,
			"transition": true,
			"expression": {
				"interpolated": true,
				"parameters": ["zoom", "global-state"]
			},
			"property-type": "data-constant"
		},
		"fill-color": {
			"type": "color",
			"default": "#000000",
			"transition": true,
			"expression": {
				"interpolated": true,
				"parameters": [
					"zoom",
					"feature",
					"feature-state"
				]
			},
			"property-type": "data-driven"
		},
		"fill-outline-color": {
			"type": "color",
			"transition": true,
			"requires": [{ "!": "fill-pattern" }, { "fill-antialias": true }],
			"expression": {
				"interpolated": true,
				"parameters": [
					"zoom",
					"feature",
					"feature-state"
				]
			},
			"property-type": "data-driven"
		},
		"fill-translate": {
			"type": "array",
			"value": "number",
			"length": 2,
			"default": [0, 0],
			"transition": true,
			"units": "pixels",
			"expression": {
				"interpolated": true,
				"parameters": ["zoom"]
			},
			"property-type": "data-constant"
		},
		"fill-translate-anchor": {
			"type": "enum",
			"values": {
				"map": {},
				"viewport": {}
			},
			"default": "map",
			"requires": ["fill-translate"],
			"expression": {
				"interpolated": false,
				"parameters": ["zoom"]
			},
			"property-type": "data-constant"
		},
		"fill-pattern": {
			"type": "resolvedImage",
			"transition": true,
			"expression": {
				"interpolated": false,
				"parameters": ["zoom", "feature"]
			},
			"property-type": "cross-faded-data-driven"
		}
	},
	"paint_fill-extrusion": {
		"fill-extrusion-opacity": {
			"type": "number",
			"default": 1,
			"minimum": 0,
			"maximum": 1,
			"transition": true,
			"expression": {
				"interpolated": true,
				"parameters": ["zoom"]
			},
			"property-type": "data-constant"
		},
		"fill-extrusion-color": {
			"type": "color",
			"default": "#000000",
			"transition": true,
			"requires": [{ "!": "fill-extrusion-pattern" }],
			"expression": {
				"interpolated": true,
				"parameters": [
					"zoom",
					"feature",
					"feature-state"
				]
			},
			"property-type": "data-driven"
		},
		"fill-extrusion-translate": {
			"type": "array",
			"value": "number",
			"length": 2,
			"default": [0, 0],
			"transition": true,
			"units": "pixels",
			"expression": {
				"interpolated": true,
				"parameters": ["zoom"]
			},
			"property-type": "data-constant"
		},
		"fill-extrusion-translate-anchor": {
			"type": "enum",
			"values": {
				"map": {},
				"viewport": {}
			},
			"default": "map",
			"requires": ["fill-extrusion-translate"],
			"expression": {
				"interpolated": false,
				"parameters": ["zoom"]
			},
			"property-type": "data-constant"
		},
		"fill-extrusion-pattern": {
			"type": "resolvedImage",
			"transition": true,
			"expression": {
				"interpolated": false,
				"parameters": ["zoom", "feature"]
			},
			"property-type": "cross-faded-data-driven"
		},
		"fill-extrusion-height": {
			"type": "number",
			"default": 0,
			"units": "meters",
			"transition": true,
			"expression": {
				"interpolated": true,
				"parameters": [
					"zoom",
					"feature",
					"feature-state"
				]
			},
			"property-type": "data-driven"
		},
		"fill-extrusion-base": {
			"type": "number",
			"default": 0,
			"units": "meters",
			"transition": true,
			"requires": ["fill-extrusion-height"],
			"expression": {
				"interpolated": true,
				"parameters": [
					"zoom",
					"feature",
					"feature-state"
				]
			},
			"property-type": "data-driven"
		},
		"fill-extrusion-vertical-gradient": {
			"type": "boolean",
			"default": true,
			"transition": false,
			"expression": {
				"interpolated": false,
				"parameters": ["zoom"]
			},
			"property-type": "data-constant"
		}
	},
	paint_line: {
		"line-opacity": {
			"type": "number",
			"default": 1,
			"minimum": 0,
			"maximum": 1,
			"transition": true,
			"expression": {
				"interpolated": true,
				"parameters": [
					"zoom",
					"feature",
					"feature-state"
				]
			},
			"property-type": "data-driven"
		},
		"line-layer-opacity": {
			"type": "number",
			"default": 1,
			"minimum": 0,
			"maximum": 1,
			"transition": true,
			"expression": {
				"interpolated": true,
				"parameters": ["zoom", "global-state"]
			},
			"property-type": "data-constant"
		},
		"line-color": {
			"type": "color",
			"default": "#000000",
			"transition": true,
			"requires": [{ "!": "line-pattern" }],
			"expression": {
				"interpolated": true,
				"parameters": [
					"zoom",
					"feature",
					"feature-state"
				]
			},
			"property-type": "data-driven"
		},
		"line-translate": {
			"type": "array",
			"value": "number",
			"length": 2,
			"default": [0, 0],
			"transition": true,
			"units": "pixels",
			"expression": {
				"interpolated": true,
				"parameters": ["zoom"]
			},
			"property-type": "data-constant"
		},
		"line-translate-anchor": {
			"type": "enum",
			"values": {
				"map": {},
				"viewport": {}
			},
			"default": "map",
			"requires": ["line-translate"],
			"expression": {
				"interpolated": false,
				"parameters": ["zoom"]
			},
			"property-type": "data-constant"
		},
		"line-width": {
			"type": "number",
			"default": 1,
			"minimum": 0,
			"transition": true,
			"units": "pixels",
			"expression": {
				"interpolated": true,
				"parameters": [
					"zoom",
					"feature",
					"feature-state"
				]
			},
			"property-type": "data-driven"
		},
		"line-gap-width": {
			"type": "number",
			"default": 0,
			"minimum": 0,
			"transition": true,
			"units": "pixels",
			"expression": {
				"interpolated": true,
				"parameters": [
					"zoom",
					"feature",
					"feature-state"
				]
			},
			"property-type": "data-driven"
		},
		"line-offset": {
			"type": "number",
			"default": 0,
			"transition": true,
			"units": "pixels",
			"expression": {
				"interpolated": true,
				"parameters": [
					"zoom",
					"feature",
					"feature-state"
				]
			},
			"property-type": "data-driven"
		},
		"line-blur": {
			"type": "number",
			"default": 0,
			"minimum": 0,
			"transition": true,
			"units": "pixels",
			"expression": {
				"interpolated": true,
				"parameters": [
					"zoom",
					"feature",
					"feature-state"
				]
			},
			"property-type": "data-driven"
		},
		"line-dasharray": {
			"type": "array",
			"value": "number",
			"minimum": 0,
			"transition": true,
			"units": "line widths",
			"requires": [{ "!": "line-pattern" }],
			"expression": {
				"interpolated": false,
				"parameters": ["zoom", "feature"]
			},
			"property-type": "cross-faded-data-driven"
		},
		"line-pattern": {
			"type": "resolvedImage",
			"transition": true,
			"expression": {
				"interpolated": false,
				"parameters": ["zoom", "feature"]
			},
			"property-type": "cross-faded-data-driven"
		},
		"line-gradient": {
			"type": "color",
			"transition": false,
			"requires": [
				{ "!": "line-dasharray" },
				{ "!": "line-pattern" },
				{
					"source": "geojson",
					"has": { "lineMetrics": true }
				}
			],
			"expression": {
				"interpolated": true,
				"parameters": ["line-progress"]
			},
			"property-type": "color-ramp"
		}
	},
	paint_circle: {
		"circle-radius": {
			"type": "number",
			"default": 5,
			"minimum": 0,
			"transition": true,
			"units": "pixels",
			"expression": {
				"interpolated": true,
				"parameters": [
					"zoom",
					"feature",
					"feature-state"
				]
			},
			"property-type": "data-driven"
		},
		"circle-color": {
			"type": "color",
			"default": "#000000",
			"transition": true,
			"expression": {
				"interpolated": true,
				"parameters": [
					"zoom",
					"feature",
					"feature-state"
				]
			},
			"property-type": "data-driven"
		},
		"circle-blur": {
			"type": "number",
			"default": 0,
			"transition": true,
			"expression": {
				"interpolated": true,
				"parameters": [
					"zoom",
					"feature",
					"feature-state"
				]
			},
			"property-type": "data-driven"
		},
		"circle-opacity": {
			"type": "number",
			"default": 1,
			"minimum": 0,
			"maximum": 1,
			"transition": true,
			"expression": {
				"interpolated": true,
				"parameters": [
					"zoom",
					"feature",
					"feature-state"
				]
			},
			"property-type": "data-driven"
		},
		"circle-translate": {
			"type": "array",
			"value": "number",
			"length": 2,
			"default": [0, 0],
			"transition": true,
			"units": "pixels",
			"expression": {
				"interpolated": true,
				"parameters": ["zoom"]
			},
			"property-type": "data-constant"
		},
		"circle-translate-anchor": {
			"type": "enum",
			"values": {
				"map": {},
				"viewport": {}
			},
			"default": "map",
			"requires": ["circle-translate"],
			"expression": {
				"interpolated": false,
				"parameters": ["zoom"]
			},
			"property-type": "data-constant"
		},
		"circle-pitch-scale": {
			"type": "enum",
			"values": {
				"map": {},
				"viewport": {}
			},
			"default": "map",
			"expression": {
				"interpolated": false,
				"parameters": ["zoom"]
			},
			"property-type": "data-constant"
		},
		"circle-pitch-alignment": {
			"type": "enum",
			"values": {
				"map": {},
				"viewport": {}
			},
			"default": "viewport",
			"expression": {
				"interpolated": false,
				"parameters": ["zoom"]
			},
			"property-type": "data-constant"
		},
		"circle-stroke-width": {
			"type": "number",
			"default": 0,
			"minimum": 0,
			"transition": true,
			"units": "pixels",
			"expression": {
				"interpolated": true,
				"parameters": [
					"zoom",
					"feature",
					"feature-state"
				]
			},
			"property-type": "data-driven"
		},
		"circle-stroke-color": {
			"type": "color",
			"default": "#000000",
			"transition": true,
			"expression": {
				"interpolated": true,
				"parameters": [
					"zoom",
					"feature",
					"feature-state"
				]
			},
			"property-type": "data-driven"
		},
		"circle-stroke-opacity": {
			"type": "number",
			"default": 1,
			"minimum": 0,
			"maximum": 1,
			"transition": true,
			"expression": {
				"interpolated": true,
				"parameters": [
					"zoom",
					"feature",
					"feature-state"
				]
			},
			"property-type": "data-driven"
		}
	},
	paint_heatmap: {
		"heatmap-radius": {
			"type": "number",
			"default": 30,
			"minimum": 1,
			"transition": true,
			"units": "pixels",
			"expression": {
				"interpolated": true,
				"parameters": [
					"zoom",
					"feature",
					"feature-state"
				]
			},
			"property-type": "data-driven"
		},
		"heatmap-weight": {
			"type": "number",
			"default": 1,
			"minimum": 0,
			"transition": false,
			"expression": {
				"interpolated": true,
				"parameters": [
					"zoom",
					"feature",
					"feature-state"
				]
			},
			"property-type": "data-driven"
		},
		"heatmap-intensity": {
			"type": "number",
			"default": 1,
			"minimum": 0,
			"transition": true,
			"expression": {
				"interpolated": true,
				"parameters": ["zoom"]
			},
			"property-type": "data-constant"
		},
		"heatmap-color": {
			"type": "color",
			"default": [
				"interpolate",
				["linear"],
				["heatmap-density"],
				0,
				"rgba(0, 0, 255, 0)",
				.1,
				"royalblue",
				.3,
				"cyan",
				.5,
				"lime",
				.7,
				"yellow",
				1,
				"red"
			],
			"transition": false,
			"expression": {
				"interpolated": true,
				"parameters": ["heatmap-density"]
			},
			"property-type": "color-ramp"
		},
		"heatmap-opacity": {
			"type": "number",
			"default": 1,
			"minimum": 0,
			"maximum": 1,
			"transition": true,
			"expression": {
				"interpolated": true,
				"parameters": ["zoom"]
			},
			"property-type": "data-constant"
		}
	},
	paint_symbol: {
		"icon-opacity": {
			"type": "number",
			"default": 1,
			"minimum": 0,
			"maximum": 1,
			"transition": true,
			"requires": ["icon-image"],
			"expression": {
				"interpolated": true,
				"parameters": [
					"zoom",
					"feature",
					"feature-state"
				]
			},
			"property-type": "data-driven"
		},
		"icon-color": {
			"type": "color",
			"default": "#000000",
			"transition": true,
			"requires": ["icon-image"],
			"expression": {
				"interpolated": true,
				"parameters": [
					"zoom",
					"feature",
					"feature-state"
				]
			},
			"property-type": "data-driven"
		},
		"icon-halo-color": {
			"type": "color",
			"default": "rgba(0, 0, 0, 0)",
			"transition": true,
			"requires": ["icon-image"],
			"expression": {
				"interpolated": true,
				"parameters": [
					"zoom",
					"feature",
					"feature-state"
				]
			},
			"property-type": "data-driven"
		},
		"icon-halo-width": {
			"type": "number",
			"default": 0,
			"minimum": 0,
			"transition": true,
			"units": "pixels",
			"requires": ["icon-image"],
			"expression": {
				"interpolated": true,
				"parameters": [
					"zoom",
					"feature",
					"feature-state"
				]
			},
			"property-type": "data-driven"
		},
		"icon-halo-blur": {
			"type": "number",
			"default": 0,
			"minimum": 0,
			"transition": true,
			"units": "pixels",
			"requires": ["icon-image"],
			"expression": {
				"interpolated": true,
				"parameters": [
					"zoom",
					"feature",
					"feature-state"
				]
			},
			"property-type": "data-driven"
		},
		"icon-translate": {
			"type": "array",
			"value": "number",
			"length": 2,
			"default": [0, 0],
			"transition": true,
			"units": "pixels",
			"requires": ["icon-image"],
			"expression": {
				"interpolated": true,
				"parameters": ["zoom"]
			},
			"property-type": "data-constant"
		},
		"icon-translate-anchor": {
			"type": "enum",
			"values": {
				"map": {},
				"viewport": {}
			},
			"default": "map",
			"requires": ["icon-image", "icon-translate"],
			"expression": {
				"interpolated": false,
				"parameters": ["zoom"]
			},
			"property-type": "data-constant"
		},
		"text-opacity": {
			"type": "number",
			"default": 1,
			"minimum": 0,
			"maximum": 1,
			"transition": true,
			"requires": ["text-field"],
			"expression": {
				"interpolated": true,
				"parameters": [
					"zoom",
					"feature",
					"feature-state"
				]
			},
			"property-type": "data-driven"
		},
		"text-color": {
			"type": "color",
			"default": "#000000",
			"transition": true,
			"overridable": true,
			"requires": ["text-field"],
			"expression": {
				"interpolated": true,
				"parameters": [
					"zoom",
					"feature",
					"feature-state"
				]
			},
			"property-type": "data-driven"
		},
		"text-halo-color": {
			"type": "color",
			"default": "rgba(0, 0, 0, 0)",
			"transition": true,
			"requires": ["text-field"],
			"expression": {
				"interpolated": true,
				"parameters": [
					"zoom",
					"feature",
					"feature-state"
				]
			},
			"property-type": "data-driven"
		},
		"text-halo-width": {
			"type": "number",
			"default": 0,
			"minimum": 0,
			"transition": true,
			"units": "pixels",
			"requires": ["text-field"],
			"expression": {
				"interpolated": true,
				"parameters": [
					"zoom",
					"feature",
					"feature-state"
				]
			},
			"property-type": "data-driven"
		},
		"text-halo-blur": {
			"type": "number",
			"default": 0,
			"minimum": 0,
			"transition": true,
			"units": "pixels",
			"requires": ["text-field"],
			"expression": {
				"interpolated": true,
				"parameters": [
					"zoom",
					"feature",
					"feature-state"
				]
			},
			"property-type": "data-driven"
		},
		"text-translate": {
			"type": "array",
			"value": "number",
			"length": 2,
			"default": [0, 0],
			"transition": true,
			"units": "pixels",
			"requires": ["text-field"],
			"expression": {
				"interpolated": true,
				"parameters": ["zoom"]
			},
			"property-type": "data-constant"
		},
		"text-translate-anchor": {
			"type": "enum",
			"values": {
				"map": {},
				"viewport": {}
			},
			"default": "map",
			"requires": ["text-field", "text-translate"],
			"expression": {
				"interpolated": false,
				"parameters": ["zoom"]
			},
			"property-type": "data-constant"
		}
	},
	paint_raster: {
		"raster-opacity": {
			"type": "number",
			"default": 1,
			"minimum": 0,
			"maximum": 1,
			"transition": true,
			"expression": {
				"interpolated": true,
				"parameters": ["zoom"]
			},
			"property-type": "data-constant"
		},
		"raster-hue-rotate": {
			"type": "number",
			"default": 0,
			"period": 360,
			"transition": true,
			"units": "degrees",
			"expression": {
				"interpolated": true,
				"parameters": ["zoom"]
			},
			"property-type": "data-constant"
		},
		"raster-brightness-min": {
			"type": "number",
			"default": 0,
			"minimum": 0,
			"maximum": 1,
			"transition": true,
			"expression": {
				"interpolated": true,
				"parameters": ["zoom"]
			},
			"property-type": "data-constant"
		},
		"raster-brightness-max": {
			"type": "number",
			"default": 1,
			"minimum": 0,
			"maximum": 1,
			"transition": true,
			"expression": {
				"interpolated": true,
				"parameters": ["zoom"]
			},
			"property-type": "data-constant"
		},
		"raster-saturation": {
			"type": "number",
			"default": 0,
			"minimum": -1,
			"maximum": 1,
			"transition": true,
			"expression": {
				"interpolated": true,
				"parameters": ["zoom"]
			},
			"property-type": "data-constant"
		},
		"raster-contrast": {
			"type": "number",
			"default": 0,
			"minimum": -1,
			"maximum": 1,
			"transition": true,
			"expression": {
				"interpolated": true,
				"parameters": ["zoom"]
			},
			"property-type": "data-constant"
		},
		"resampling": {
			"type": "enum",
			"values": {
				"linear": {},
				"nearest": {}
			},
			"default": "linear",
			"expression": {
				"interpolated": false,
				"parameters": ["zoom"]
			},
			"property-type": "data-constant"
		},
		"raster-resampling": {
			"type": "enum",
			"values": {
				"linear": {},
				"nearest": {}
			},
			"default": "linear",
			"expression": {
				"interpolated": false,
				"parameters": ["zoom"]
			},
			"property-type": "data-constant"
		},
		"raster-fade-duration": {
			"type": "number",
			"default": 300,
			"minimum": 0,
			"transition": false,
			"units": "milliseconds",
			"expression": {
				"interpolated": true,
				"parameters": ["zoom"]
			},
			"property-type": "data-constant"
		}
	},
	paint_hillshade: {
		"hillshade-illumination-direction": {
			"type": "numberArray",
			"default": 335,
			"minimum": 0,
			"maximum": 359,
			"transition": false,
			"expression": {
				"interpolated": true,
				"parameters": ["zoom"]
			},
			"property-type": "data-constant"
		},
		"hillshade-illumination-altitude": {
			"type": "numberArray",
			"default": 45,
			"minimum": 0,
			"maximum": 90,
			"transition": false,
			"expression": {
				"interpolated": true,
				"parameters": ["zoom"]
			},
			"property-type": "data-constant"
		},
		"hillshade-illumination-anchor": {
			"type": "enum",
			"values": {
				"map": {},
				"viewport": {}
			},
			"default": "viewport",
			"expression": {
				"interpolated": false,
				"parameters": ["zoom"]
			},
			"property-type": "data-constant"
		},
		"hillshade-exaggeration": {
			"type": "number",
			"default": .5,
			"minimum": 0,
			"maximum": 1,
			"transition": true,
			"expression": {
				"interpolated": true,
				"parameters": ["zoom"]
			},
			"property-type": "data-constant"
		},
		"hillshade-shadow-color": {
			"type": "colorArray",
			"default": "#000000",
			"transition": true,
			"expression": {
				"interpolated": true,
				"parameters": ["zoom"]
			},
			"property-type": "data-constant"
		},
		"hillshade-highlight-color": {
			"type": "colorArray",
			"default": "#FFFFFF",
			"transition": true,
			"expression": {
				"interpolated": true,
				"parameters": ["zoom"]
			},
			"property-type": "data-constant"
		},
		"hillshade-accent-color": {
			"type": "color",
			"default": "#000000",
			"transition": true,
			"expression": {
				"interpolated": true,
				"parameters": ["zoom"]
			},
			"property-type": "data-constant"
		},
		"hillshade-method": {
			"type": "enum",
			"values": {
				"standard": {},
				"basic": {},
				"combined": {},
				"igor": {},
				"multidirectional": {}
			},
			"default": "standard",
			"expression": {
				"interpolated": false,
				"parameters": ["zoom"]
			},
			"property-type": "data-constant"
		},
		"resampling": {
			"type": "enum",
			"values": {
				"linear": {},
				"nearest": {}
			},
			"default": "linear",
			"expression": {
				"interpolated": false,
				"parameters": ["zoom"]
			},
			"property-type": "data-constant"
		}
	},
	"paint_color-relief": {
		"color-relief-opacity": {
			"type": "number",
			"default": 1,
			"minimum": 0,
			"maximum": 1,
			"transition": true,
			"expression": {
				"interpolated": true,
				"parameters": ["zoom"]
			},
			"property-type": "data-constant"
		},
		"color-relief-color": {
			"type": "color",
			"transition": false,
			"expression": {
				"interpolated": true,
				"parameters": ["elevation"]
			},
			"property-type": "color-ramp"
		},
		"resampling": {
			"type": "enum",
			"values": {
				"linear": {},
				"nearest": {}
			},
			"default": "linear",
			"expression": {
				"interpolated": false,
				"parameters": ["zoom"]
			},
			"property-type": "data-constant"
		}
	},
	paint_background: {
		"background-color": {
			"type": "color",
			"default": "#000000",
			"transition": true,
			"requires": [{ "!": "background-pattern" }],
			"expression": {
				"interpolated": true,
				"parameters": ["zoom"]
			},
			"property-type": "data-constant"
		},
		"background-pattern": {
			"type": "resolvedImage",
			"transition": true,
			"expression": {
				"interpolated": false,
				"parameters": ["zoom"]
			},
			"property-type": "cross-faded"
		},
		"background-opacity": {
			"type": "number",
			"default": 1,
			"minimum": 0,
			"maximum": 1,
			"transition": true,
			"expression": {
				"interpolated": true,
				"parameters": ["zoom"]
			},
			"property-type": "data-constant"
		}
	},
	transition: {
		"duration": {
			"type": "number",
			"default": 300,
			"minimum": 0,
			"units": "milliseconds"
		},
		"delay": {
			"type": "number",
			"default": 0,
			"minimum": 0,
			"units": "milliseconds"
		}
	},
	"property-type": {
		"data-driven": { "type": "property-type" },
		"cross-faded": { "type": "property-type" },
		"cross-faded-data-driven": { "type": "property-type" },
		"color-ramp": { "type": "property-type" },
		"data-constant": { "type": "property-type" },
		"constant": { "type": "property-type" }
	},
	promoteId: { "*": { "type": "string" } },
	interpolation: {
		"type": "array",
		"value": "interpolation_name",
		"minimum": 1
	},
	interpolation_name: {
		"type": "enum",
		"values": {
			"linear": { "syntax": {
				"overloads": [{
					"parameters": [],
					"output-type": "interpolation"
				}],
				"parameters": []
			} },
			"exponential": { "syntax": {
				"overloads": [{
					"parameters": ["base"],
					"output-type": "interpolation"
				}],
				"parameters": [{
					"name": "base",
					"type": "number literal"
				}]
			} },
			"cubic-bezier": { "syntax": {
				"overloads": [{
					"parameters": [
						"x1",
						"y1",
						"x2",
						"y2"
					],
					"output-type": "interpolation"
				}],
				"parameters": [
					{
						"name": "x1",
						"type": "number literal"
					},
					{
						"name": "y1",
						"type": "number literal"
					},
					{
						"name": "x2",
						"type": "number literal"
					},
					{
						"name": "y2",
						"type": "number literal"
					}
				]
			} }
		}
	}
};
//#endregion
//#region src/reference/latest.ts
const latest = v8_default;
//#endregion
//#region node_modules/json-stringify-pretty-compact/index.js
const stringOrChar = /("(?:[^\\"]|\\.)*")|[:,]/g;
function stringify(passedObj, options = {}) {
	const indent = JSON.stringify([1], void 0, options.indent === void 0 ? 2 : options.indent).slice(2, -3);
	const maxLength = indent === "" ? Infinity : options.maxLength === void 0 ? 80 : options.maxLength;
	let { replacer } = options;
	return (function _stringify(obj, currentIndent, reserved) {
		if (obj && typeof obj.toJSON === "function") obj = obj.toJSON();
		const string = JSON.stringify(obj, replacer);
		if (string === void 0) return string;
		const length = maxLength - currentIndent.length - reserved;
		if (string.length <= length) {
			const prettified = string.replace(stringOrChar, (match, stringLiteral) => {
				return stringLiteral || `${match} `;
			});
			if (prettified.length <= length) return prettified;
		}
		if (replacer != null) {
			obj = JSON.parse(string);
			replacer = void 0;
		}
		if (typeof obj === "object" && obj !== null) {
			const nextIndent = currentIndent + indent;
			const items = [];
			let index = 0;
			let start;
			let end;
			if (Array.isArray(obj)) {
				start = "[";
				end = "]";
				const { length } = obj;
				for (; index < length; index++) items.push(_stringify(obj[index], nextIndent, index === length - 1 ? 0 : 1) || "null");
			} else {
				start = "{";
				end = "}";
				const keys = Object.keys(obj);
				const { length } = keys;
				for (; index < length; index++) {
					const key = keys[index];
					const keyPart = `${JSON.stringify(key)}: `;
					const value = _stringify(obj[key], nextIndent, keyPart.length + (index === length - 1 ? 0 : 1));
					if (value !== void 0) items.push(keyPart + value);
				}
			}
			if (items.length > 0) return [
				start,
				indent + items.join(`,\n${nextIndent}`),
				end
			].join(`\n${currentIndent}`);
		}
		return string;
	})(passedObj, "", 0);
}
//#endregion
//#region src/format.ts
function sortKeysBy(obj, reference) {
	const result = {};
	for (const key in reference) if (obj[key] !== void 0) result[key] = obj[key];
	for (const key in obj) if (result[key] === void 0) result[key] = obj[key];
	return result;
}
/**
* Format a MapLibre Style.  Returns a stringified style with its keys
* sorted in the same order as the reference style.
*
* The optional `space` argument is passed to
* [`JSON.stringify`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/JSON/stringify)
* to generate formatted output.
*
* If `space` is unspecified, a default of `2` spaces will be used.
*
* @private
* @param {Object} style a MapLibre Style
* @param {number} [space] space argument to pass to `JSON.stringify`
* @returns {string} stringified formatted JSON
* @example
* var fs = require('fs');
* var format = require('maplibre-gl-style-spec').format;
* var style = fs.readFileSync('./source.json', 'utf8');
* fs.writeFileSync('./dest.json', format(style));
* fs.writeFileSync('./dest.min.json', format(style, 0));
*/
function format(style, space = 2) {
	style = sortKeysBy(style, latest.$root);
	if (style.layers) style.layers = style.layers.map((layer) => sortKeysBy(layer, latest.layer));
	return stringify(style, { indent: space });
}
//#endregion
//#region src/visit.ts
function getPropertyReference(propertyName) {
	for (let i = 0; i < v8_default.layout.length; i++) for (const key in v8_default[v8_default.layout[i]]) if (key === propertyName) return v8_default[v8_default.layout[i]][key];
	for (let i = 0; i < v8_default.paint.length; i++) for (const key in v8_default[v8_default.paint[i]]) if (key === propertyName) return v8_default[v8_default.paint[i]][key];
	return null;
}
function eachSource(style, callback) {
	for (const k in style.sources) callback(style.sources[k]);
}
function eachLayer(style, callback) {
	for (const layer of style.layers) callback(layer);
}
function eachProperty(style, options, callback) {
	function inner(layer, propertyType) {
		const properties = layer[propertyType];
		if (!properties) return;
		Object.keys(properties).forEach((key) => {
			callback({
				path: [
					layer.id,
					propertyType,
					key
				],
				key,
				value: properties[key],
				reference: getPropertyReference(key),
				set(x) {
					properties[key] = x;
				}
			});
		});
	}
	eachLayer(style, (layer) => {
		if (options.paint) inner(layer, "paint");
		if (options.layout) inner(layer, "layout");
	});
}
//#endregion
//#region src/migrate/v8.ts
function eachLayout(layer, callback) {
	for (const k in layer) if (k.indexOf("layout") === 0) callback(layer[k], k);
}
function eachPaint(layer, callback) {
	for (const k in layer) if (k.indexOf("paint") === 0) callback(layer[k], k);
}
function resolveConstant(style, value) {
	if (typeof value === "string" && value[0] === "@") return resolveConstant(style, style.constants[value]);
	else return value;
}
function isFunction(value) {
	return Array.isArray(value.stops);
}
function renameProperty(obj, from, to) {
	obj[to] = obj[from];
	delete obj[from];
}
function migrateV8(style) {
	style.version = 8;
	eachSource(style, (source) => {
		if (source.type === "video" && source["url"] !== void 0) renameProperty(source, "url", "urls");
		if (source.type === "video") source.coordinates.forEach((coord) => {
			return coord.reverse();
		});
	});
	eachLayer(style, (layer) => {
		eachLayout(layer, (layout) => {
			if (layout["symbol-min-distance"] !== void 0) renameProperty(layout, "symbol-min-distance", "symbol-spacing");
		});
		eachPaint(layer, (paint) => {
			if (paint["background-image"] !== void 0) renameProperty(paint, "background-image", "background-pattern");
			if (paint["line-image"] !== void 0) renameProperty(paint, "line-image", "line-pattern");
			if (paint["fill-image"] !== void 0) renameProperty(paint, "fill-image", "fill-pattern");
		});
	});
	eachProperty(style, {
		paint: true,
		layout: true
	}, (property) => {
		const value = resolveConstant(style, property.value);
		if (isFunction(value)) value.stops.forEach((stop) => {
			stop[1] = resolveConstant(style, stop[1]);
		});
		property.set(value);
	});
	delete style["constants"];
	eachLayer(style, (layer) => {
		eachLayout(layer, (layout) => {
			delete layout["text-max-size"];
			delete layout["icon-max-size"];
		});
		eachPaint(layer, (paint) => {
			if (paint["text-size"]) {
				if (!layer.layout) layer.layout = {};
				layer.layout["text-size"] = paint["text-size"];
				delete paint["text-size"];
			}
			if (paint["icon-size"]) {
				if (!layer.layout) layer.layout = {};
				layer.layout["icon-size"] = paint["icon-size"];
				delete paint["icon-size"];
			}
		});
	});
	function migrateFontStack(font) {
		function splitAndTrim(string) {
			return string.split(",").map((s) => {
				return s.trim();
			});
		}
		if (Array.isArray(font)) return font;
		else if (typeof font === "string") return splitAndTrim(font);
		else if (typeof font === "object") {
			font.stops.forEach((stop) => {
				stop[1] = splitAndTrim(stop[1]);
			});
			return font;
		} else throw new Error("unexpected font value");
	}
	eachLayer(style, (layer) => {
		eachLayout(layer, (layout) => {
			if (layout["text-font"]) layout["text-font"] = migrateFontStack(layout["text-font"]);
		});
	});
	let firstSymbolLayer = 0;
	for (let i = style.layers.length - 1; i >= 0; i--) if (style.layers[i].type !== "symbol") {
		firstSymbolLayer = i + 1;
		break;
	}
	const symbolLayers = style.layers.splice(firstSymbolLayer);
	symbolLayers.reverse();
	style.layers = style.layers.concat(symbolLayers);
	return style;
}
//#endregion
//#region src/expression/types.ts
const NullType = { kind: "null" };
const NumberType = { kind: "number" };
const StringType = { kind: "string" };
const BooleanType = { kind: "boolean" };
const ColorType = { kind: "color" };
const ProjectionDefinitionType = { kind: "projectionDefinition" };
const ObjectType = { kind: "object" };
const ValueType = { kind: "value" };
const CollatorType = { kind: "collator" };
const FormattedType = { kind: "formatted" };
const PaddingType = { kind: "padding" };
const ColorArrayType = { kind: "colorArray" };
const NumberArrayType = { kind: "numberArray" };
const ResolvedImageType = { kind: "resolvedImage" };
const VariableAnchorOffsetCollectionType = { kind: "variableAnchorOffsetCollection" };
function array(itemType, N) {
	return {
		kind: "array",
		itemType,
		N
	};
}
function typeToString(type) {
	if (type.kind === "array") {
		const itemType = typeToString(type.itemType);
		return typeof type.N === "number" ? `array<${itemType}, ${type.N}>` : type.itemType.kind === "value" ? "array" : `array<${itemType}>`;
	} else return type.kind;
}
const valueMemberTypes = [
	NullType,
	NumberType,
	StringType,
	BooleanType,
	ColorType,
	ProjectionDefinitionType,
	FormattedType,
	ObjectType,
	array(ValueType),
	PaddingType,
	NumberArrayType,
	ColorArrayType,
	ResolvedImageType,
	VariableAnchorOffsetCollectionType
];
/**
* Returns null if `t` is a subtype of `expected`; otherwise returns an
* error message.
* @private
*/
function checkSubtype(expected, t) {
	if (t.kind === "error") return null;
	else if (expected.kind === "array") {
		if (t.kind === "array" && (t.N === 0 && t.itemType.kind === "value" || !checkSubtype(expected.itemType, t.itemType)) && (typeof expected.N !== "number" || expected.N === t.N)) return null;
	} else if (expected.kind === t.kind) return null;
	else if (expected.kind === "value") {
		for (const memberType of valueMemberTypes) if (!checkSubtype(memberType, t)) return null;
	}
	return `Expected ${typeToString(expected)} but found ${typeToString(t)} instead.`;
}
function isValidType(provided, allowedTypes) {
	return allowedTypes.some((t) => t.kind === provided.kind);
}
function isValidNativeType(provided, allowedTypes) {
	return allowedTypes.some((t) => {
		if (t === "null") return provided === null;
		else if (t === "array") return Array.isArray(provided);
		else if (t === "object") return provided && !Array.isArray(provided) && typeof provided === "object";
		else return t === typeof provided;
	});
}
/**
* Verify whether the specified type is of the same type as the specified sample.
*
* @param provided Type to verify
* @param sample Sample type to reference
* @returns `true` if both objects are of the same type, `false` otherwise
* @example basic types
* if (verifyType(outputType, ValueType)) {
*     // type narrowed to:
*     outputType.kind; // 'value'
* }
* @example array types
* if (verifyType(outputType, array(NumberType))) {
*     // type narrowed to:
*     outputType.kind; // 'array'
*     outputType.itemType; // NumberTypeT
*     outputType.itemType.kind; // 'number'
* }
*/
function verifyType(provided, sample) {
	if (provided.kind === "array" && sample.kind === "array") return provided.itemType.kind === sample.itemType.kind && typeof provided.N === "number";
	return provided.kind === sample.kind;
}
//#endregion
//#region src/expression/types/color_spaces.ts
const Xn = .96422;
const Yn = 1;
const Zn = .82521;
const t0 = 4 / 29;
const t1 = 6 / 29;
const t2 = 3 * t1 * t1;
const t3 = t1 * t1 * t1;
const deg2rad = Math.PI / 180;
const rad2deg = 180 / Math.PI;
function constrainAngle(angle) {
	angle = angle % 360;
	if (angle < 0) angle += 360;
	return angle;
}
function rgbToLab([r, g, b, alpha]) {
	r = rgb2xyz(r);
	g = rgb2xyz(g);
	b = rgb2xyz(b);
	let x, z;
	const y = xyz2lab((.2225045 * r + .7168786 * g + .0606169 * b) / Yn);
	if (r === g && g === b) x = z = y;
	else {
		x = xyz2lab((.4360747 * r + .3850649 * g + .1430804 * b) / Xn);
		z = xyz2lab((.0139322 * r + .0971045 * g + .7141733 * b) / Zn);
	}
	const l = 116 * y - 16;
	return [
		l < 0 ? 0 : l,
		500 * (x - y),
		200 * (y - z),
		alpha
	];
}
function rgb2xyz(x) {
	return x <= .04045 ? x / 12.92 : Math.pow((x + .055) / 1.055, 2.4);
}
function xyz2lab(t) {
	return t > t3 ? Math.pow(t, 1 / 3) : t / t2 + t0;
}
function labToRgb([l, a, b, alpha]) {
	let y = (l + 16) / 116, x = isNaN(a) ? y : y + a / 500, z = isNaN(b) ? y : y - b / 200;
	y = Yn * lab2xyz(y);
	x = Xn * lab2xyz(x);
	z = Zn * lab2xyz(z);
	return [
		xyz2rgb(3.1338561 * x - 1.6168667 * y - .4906146 * z),
		xyz2rgb(-.9787684 * x + 1.9161415 * y + .033454 * z),
		xyz2rgb(.0719453 * x - .2289914 * y + 1.4052427 * z),
		alpha
	];
}
function xyz2rgb(x) {
	x = x <= .00304 ? 12.92 * x : 1.055 * Math.pow(x, 1 / 2.4) - .055;
	return x < 0 ? 0 : x > 1 ? 1 : x;
}
function lab2xyz(t) {
	return t > t1 ? t * t * t : t2 * (t - t0);
}
function rgbToHcl(rgbColor) {
	const [l, a, b, alpha] = rgbToLab(rgbColor);
	const c = Math.sqrt(a * a + b * b);
	return [
		Math.round(c * 1e4) ? constrainAngle(Math.atan2(b, a) * rad2deg) : NaN,
		c,
		l,
		alpha
	];
}
function hclToRgb([h, c, l, alpha]) {
	h = isNaN(h) ? 0 : h * deg2rad;
	return labToRgb([
		l,
		Math.cos(h) * c,
		Math.sin(h) * c,
		alpha
	]);
}
function hslToRgb([h, s, l, alpha]) {
	h = constrainAngle(h);
	s /= 100;
	l /= 100;
	function f(n) {
		const k = (n + h / 30) % 12;
		const a = s * Math.min(l, 1 - l);
		return l - a * Math.max(-1, Math.min(k - 3, 9 - k, 1));
	}
	return [
		f(0),
		f(8),
		f(4),
		alpha
	];
}
//#endregion
//#region src/util/get_own.ts
const hasOwnProperty = Object.hasOwn || function hasOwnProperty(object, key) {
	return Object.prototype.hasOwnProperty.call(object, key);
};
function getOwn(object, key) {
	return hasOwnProperty(object, key) ? object[key] : void 0;
}
//#endregion
//#region src/expression/types/parse_css_color.ts
/**
* CSS color parser compliant with CSS Color 4 Specification.
* Supports: named colors, `transparent` keyword, all rgb hex notations,
* rgb(), rgba(), hsl() and hsla() functions.
* Does not round the parsed values to integers from the range 0..255.
*
* Syntax:
*
* <alpha-value> = <number> | <percentage>
*         <hue> = <number> | <angle>
*
*         rgb() = rgb( <percentage>{3} [ / <alpha-value> ]? ) | rgb( <number>{3} [ / <alpha-value> ]? )
*         rgb() = rgb( <percentage>#{3} , <alpha-value>? )    | rgb( <number>#{3} , <alpha-value>? )
*
*         hsl() = hsl( <hue> <percentage> <percentage> [ / <alpha-value> ]? )
*         hsl() = hsl( <hue>, <percentage>, <percentage>, <alpha-value>? )
*
* Caveats:
*   - <angle> - <number> with optional `deg` suffix; `grad`, `rad`, `turn` are not supported
*   - `none` keyword is not supported
*   - comments inside rgb()/hsl() are not supported
*   - legacy color syntax rgba() is supported with an identical grammar and behavior to rgb()
*   - legacy color syntax hsla() is supported with an identical grammar and behavior to hsl()
*
* @param input CSS color string to parse.
* @returns Color in sRGB color space, with `red`, `green`, `blue`
* and `alpha` channels normalized to the range 0..1,
* or `undefined` if the input is not a valid color string.
*/
function parseCssColor(input) {
	input = input.toLowerCase().trim();
	if (input === "transparent") return [
		0,
		0,
		0,
		0
	];
	const namedColorsMatch = getOwn(namedColors, input);
	if (namedColorsMatch) {
		const [r, g, b] = namedColorsMatch;
		return [
			r / 255,
			g / 255,
			b / 255,
			1
		];
	}
	if (input.startsWith("#")) {
		if (/^#(?:[0-9a-f]{3,4}|[0-9a-f]{6}|[0-9a-f]{8})$/.test(input)) {
			const step = input.length < 6 ? 1 : 2;
			let i = 1;
			return [
				parseHex(input.slice(i, i += step)),
				parseHex(input.slice(i, i += step)),
				parseHex(input.slice(i, i += step)),
				parseHex(input.slice(i, i + step) || "ff")
			];
		}
	}
	if (input.startsWith("rgb")) {
		const rgbMatch = input.match(/^rgba?\(\s*([\de.+-]+)(%)?(?:\s+|\s*(,)\s*)([\de.+-]+)(%)?(?:\s+|\s*(,)\s*)([\de.+-]+)(%)?(?:\s*([,\/])\s*([\de.+-]+)(%)?)?\s*\)$/);
		if (rgbMatch) {
			const [_, r, rp, f1, g, gp, f2, b, bp, f3, a, ap] = rgbMatch;
			const argFormat = [
				f1 || " ",
				f2 || " ",
				f3
			].join("");
			if (argFormat === "  " || argFormat === "  /" || argFormat === ",," || argFormat === ",,,") {
				const valFormat = [
					rp,
					gp,
					bp
				].join("");
				const maxValue = valFormat === "%%%" ? 100 : valFormat === "" ? 255 : 0;
				if (maxValue) {
					const rgba = [
						clamp(+r / maxValue, 0, 1),
						clamp(+g / maxValue, 0, 1),
						clamp(+b / maxValue, 0, 1),
						a ? parseAlpha(+a, ap) : 1
					];
					if (validateNumbers(rgba)) return rgba;
				}
			}
			return;
		}
	}
	const hslMatch = input.match(/^hsla?\(\s*([\de.+-]+)(?:deg)?(?:\s+|\s*(,)\s*)([\de.+-]+)%(?:\s+|\s*(,)\s*)([\de.+-]+)%(?:\s*([,\/])\s*([\de.+-]+)(%)?)?\s*\)$/);
	if (hslMatch) {
		const [_, h, f1, s, f2, l, f3, a, ap] = hslMatch;
		const argFormat = [
			f1 || " ",
			f2 || " ",
			f3
		].join("");
		if (argFormat === "  " || argFormat === "  /" || argFormat === ",," || argFormat === ",,,") {
			const hsla = [
				+h,
				clamp(+s, 0, 100),
				clamp(+l, 0, 100),
				a ? parseAlpha(+a, ap) : 1
			];
			if (validateNumbers(hsla)) return hslToRgb(hsla);
		}
	}
}
function parseHex(hex) {
	return parseInt(hex.padEnd(2, hex), 16) / 255;
}
function parseAlpha(a, asPercentage) {
	return clamp(asPercentage ? a / 100 : a, 0, 1);
}
function clamp(n, min, max) {
	return Math.min(Math.max(min, n), max);
}
/**
* The regular expression for numeric values is not super specific, and it may
* happen that it will accept a value that is not a valid number. In order to
* detect and eliminate such values this function exists.
*
* @param array Array of uncertain numbers.
* @returns `true` if the specified array contains only valid numbers, `false` otherwise.
*/
function validateNumbers(array) {
	return !array.some(Number.isNaN);
}
/**
* To generate:
* - visit {@link https://www.w3.org/TR/css-color-4/#named-colors}
* - run in the console:
* @example
* copy(`{\n${[...document.querySelector('.named-color-table tbody').children].map((tr) => `${tr.cells[2].textContent.trim()}: [${tr.cells[4].textContent.trim().split(/\s+/).join(', ')}],`).join('\n')}\n}`);
*/
const namedColors = {
	aliceblue: [
		240,
		248,
		255
	],
	antiquewhite: [
		250,
		235,
		215
	],
	aqua: [
		0,
		255,
		255
	],
	aquamarine: [
		127,
		255,
		212
	],
	azure: [
		240,
		255,
		255
	],
	beige: [
		245,
		245,
		220
	],
	bisque: [
		255,
		228,
		196
	],
	black: [
		0,
		0,
		0
	],
	blanchedalmond: [
		255,
		235,
		205
	],
	blue: [
		0,
		0,
		255
	],
	blueviolet: [
		138,
		43,
		226
	],
	brown: [
		165,
		42,
		42
	],
	burlywood: [
		222,
		184,
		135
	],
	cadetblue: [
		95,
		158,
		160
	],
	chartreuse: [
		127,
		255,
		0
	],
	chocolate: [
		210,
		105,
		30
	],
	coral: [
		255,
		127,
		80
	],
	cornflowerblue: [
		100,
		149,
		237
	],
	cornsilk: [
		255,
		248,
		220
	],
	crimson: [
		220,
		20,
		60
	],
	cyan: [
		0,
		255,
		255
	],
	darkblue: [
		0,
		0,
		139
	],
	darkcyan: [
		0,
		139,
		139
	],
	darkgoldenrod: [
		184,
		134,
		11
	],
	darkgray: [
		169,
		169,
		169
	],
	darkgreen: [
		0,
		100,
		0
	],
	darkgrey: [
		169,
		169,
		169
	],
	darkkhaki: [
		189,
		183,
		107
	],
	darkmagenta: [
		139,
		0,
		139
	],
	darkolivegreen: [
		85,
		107,
		47
	],
	darkorange: [
		255,
		140,
		0
	],
	darkorchid: [
		153,
		50,
		204
	],
	darkred: [
		139,
		0,
		0
	],
	darksalmon: [
		233,
		150,
		122
	],
	darkseagreen: [
		143,
		188,
		143
	],
	darkslateblue: [
		72,
		61,
		139
	],
	darkslategray: [
		47,
		79,
		79
	],
	darkslategrey: [
		47,
		79,
		79
	],
	darkturquoise: [
		0,
		206,
		209
	],
	darkviolet: [
		148,
		0,
		211
	],
	deeppink: [
		255,
		20,
		147
	],
	deepskyblue: [
		0,
		191,
		255
	],
	dimgray: [
		105,
		105,
		105
	],
	dimgrey: [
		105,
		105,
		105
	],
	dodgerblue: [
		30,
		144,
		255
	],
	firebrick: [
		178,
		34,
		34
	],
	floralwhite: [
		255,
		250,
		240
	],
	forestgreen: [
		34,
		139,
		34
	],
	fuchsia: [
		255,
		0,
		255
	],
	gainsboro: [
		220,
		220,
		220
	],
	ghostwhite: [
		248,
		248,
		255
	],
	gold: [
		255,
		215,
		0
	],
	goldenrod: [
		218,
		165,
		32
	],
	gray: [
		128,
		128,
		128
	],
	green: [
		0,
		128,
		0
	],
	greenyellow: [
		173,
		255,
		47
	],
	grey: [
		128,
		128,
		128
	],
	honeydew: [
		240,
		255,
		240
	],
	hotpink: [
		255,
		105,
		180
	],
	indianred: [
		205,
		92,
		92
	],
	indigo: [
		75,
		0,
		130
	],
	ivory: [
		255,
		255,
		240
	],
	khaki: [
		240,
		230,
		140
	],
	lavender: [
		230,
		230,
		250
	],
	lavenderblush: [
		255,
		240,
		245
	],
	lawngreen: [
		124,
		252,
		0
	],
	lemonchiffon: [
		255,
		250,
		205
	],
	lightblue: [
		173,
		216,
		230
	],
	lightcoral: [
		240,
		128,
		128
	],
	lightcyan: [
		224,
		255,
		255
	],
	lightgoldenrodyellow: [
		250,
		250,
		210
	],
	lightgray: [
		211,
		211,
		211
	],
	lightgreen: [
		144,
		238,
		144
	],
	lightgrey: [
		211,
		211,
		211
	],
	lightpink: [
		255,
		182,
		193
	],
	lightsalmon: [
		255,
		160,
		122
	],
	lightseagreen: [
		32,
		178,
		170
	],
	lightskyblue: [
		135,
		206,
		250
	],
	lightslategray: [
		119,
		136,
		153
	],
	lightslategrey: [
		119,
		136,
		153
	],
	lightsteelblue: [
		176,
		196,
		222
	],
	lightyellow: [
		255,
		255,
		224
	],
	lime: [
		0,
		255,
		0
	],
	limegreen: [
		50,
		205,
		50
	],
	linen: [
		250,
		240,
		230
	],
	magenta: [
		255,
		0,
		255
	],
	maroon: [
		128,
		0,
		0
	],
	mediumaquamarine: [
		102,
		205,
		170
	],
	mediumblue: [
		0,
		0,
		205
	],
	mediumorchid: [
		186,
		85,
		211
	],
	mediumpurple: [
		147,
		112,
		219
	],
	mediumseagreen: [
		60,
		179,
		113
	],
	mediumslateblue: [
		123,
		104,
		238
	],
	mediumspringgreen: [
		0,
		250,
		154
	],
	mediumturquoise: [
		72,
		209,
		204
	],
	mediumvioletred: [
		199,
		21,
		133
	],
	midnightblue: [
		25,
		25,
		112
	],
	mintcream: [
		245,
		255,
		250
	],
	mistyrose: [
		255,
		228,
		225
	],
	moccasin: [
		255,
		228,
		181
	],
	navajowhite: [
		255,
		222,
		173
	],
	navy: [
		0,
		0,
		128
	],
	oldlace: [
		253,
		245,
		230
	],
	olive: [
		128,
		128,
		0
	],
	olivedrab: [
		107,
		142,
		35
	],
	orange: [
		255,
		165,
		0
	],
	orangered: [
		255,
		69,
		0
	],
	orchid: [
		218,
		112,
		214
	],
	palegoldenrod: [
		238,
		232,
		170
	],
	palegreen: [
		152,
		251,
		152
	],
	paleturquoise: [
		175,
		238,
		238
	],
	palevioletred: [
		219,
		112,
		147
	],
	papayawhip: [
		255,
		239,
		213
	],
	peachpuff: [
		255,
		218,
		185
	],
	peru: [
		205,
		133,
		63
	],
	pink: [
		255,
		192,
		203
	],
	plum: [
		221,
		160,
		221
	],
	powderblue: [
		176,
		224,
		230
	],
	purple: [
		128,
		0,
		128
	],
	rebeccapurple: [
		102,
		51,
		153
	],
	red: [
		255,
		0,
		0
	],
	rosybrown: [
		188,
		143,
		143
	],
	royalblue: [
		65,
		105,
		225
	],
	saddlebrown: [
		139,
		69,
		19
	],
	salmon: [
		250,
		128,
		114
	],
	sandybrown: [
		244,
		164,
		96
	],
	seagreen: [
		46,
		139,
		87
	],
	seashell: [
		255,
		245,
		238
	],
	sienna: [
		160,
		82,
		45
	],
	silver: [
		192,
		192,
		192
	],
	skyblue: [
		135,
		206,
		235
	],
	slateblue: [
		106,
		90,
		205
	],
	slategray: [
		112,
		128,
		144
	],
	slategrey: [
		112,
		128,
		144
	],
	snow: [
		255,
		250,
		250
	],
	springgreen: [
		0,
		255,
		127
	],
	steelblue: [
		70,
		130,
		180
	],
	tan: [
		210,
		180,
		140
	],
	teal: [
		0,
		128,
		128
	],
	thistle: [
		216,
		191,
		216
	],
	tomato: [
		255,
		99,
		71
	],
	turquoise: [
		64,
		224,
		208
	],
	violet: [
		238,
		130,
		238
	],
	wheat: [
		245,
		222,
		179
	],
	white: [
		255,
		255,
		255
	],
	whitesmoke: [
		245,
		245,
		245
	],
	yellow: [
		255,
		255,
		0
	],
	yellowgreen: [
		154,
		205,
		50
	]
};
//#endregion
//#region src/util/interpolate-primitives.ts
function interpolateNumber(from, to, t) {
	return from + t * (to - from);
}
function interpolateArray(from, to, t) {
	return from.map((d, i) => {
		return interpolateNumber(d, to[i], t);
	});
}
//#endregion
//#region src/expression/types/color.ts
/**
* Color representation used by WebGL.
* Defined in sRGB color space and pre-blended with alpha.
* @private
*/
var Color = class Color {
	/**
	* @param r Red component premultiplied by `alpha` 0..1
	* @param g Green component premultiplied by `alpha` 0..1
	* @param b Blue component premultiplied by `alpha` 0..1
	* @param [alpha=1] Alpha component 0..1
	* @param [premultiplied=true] Whether the `r`, `g` and `b` values have already
	* been multiplied by alpha. If `true` nothing happens if `false` then they will
	* be multiplied automatically.
	*/
	constructor(r, g, b, alpha = 1, premultiplied = true) {
		this.r = r;
		this.g = g;
		this.b = b;
		this.a = alpha;
		if (!premultiplied) {
			this.r *= alpha;
			this.g *= alpha;
			this.b *= alpha;
			if (!alpha) this.overwriteGetter("rgb", [
				r,
				g,
				b,
				alpha
			]);
		}
	}
	static {
		this.black = new Color(0, 0, 0, 1);
	}
	static {
		this.white = new Color(1, 1, 1, 1);
	}
	static {
		this.transparent = new Color(0, 0, 0, 0);
	}
	static {
		this.red = new Color(1, 0, 0, 1);
	}
	/**
	* Parses CSS color strings and converts colors to sRGB color space if needed.
	* Officially supported color formats:
	* - keyword, e.g. 'aquamarine' or 'steelblue'
	* - hex (with 3, 4, 6 or 8 digits), e.g. '#f0f' or '#e9bebea9'
	* - rgb and rgba, e.g. 'rgb(0,240,120)' or 'rgba(0%,94%,47%,0.1)' or 'rgb(0 240 120 / .3)'
	* - hsl and hsla, e.g. 'hsl(0,0%,83%)' or 'hsla(0,0%,83%,.5)' or 'hsl(0 0% 83% / 20%)'
	*
	* @param input CSS color string to parse.
	* @returns A `Color` instance, or `undefined` if the input is not a valid color string.
	*/
	static parse(input) {
		if (input instanceof Color) return input;
		if (typeof input !== "string") return;
		const rgba = parseCssColor(input);
		if (rgba) return new Color(...rgba, false);
	}
	/**
	* Used in color interpolation and by 'to-rgba' expression.
	*
	* @returns Gien color, with reversed alpha blending, in sRGB color space.
	*/
	get rgb() {
		const { r, g, b, a } = this;
		const f = a || Infinity;
		return this.overwriteGetter("rgb", [
			r / f,
			g / f,
			b / f,
			a
		]);
	}
	/**
	* Used in color interpolation.
	*
	* @returns Gien color, with reversed alpha blending, in HCL color space.
	*/
	get hcl() {
		return this.overwriteGetter("hcl", rgbToHcl(this.rgb));
	}
	/**
	* Used in color interpolation.
	*
	* @returns Gien color, with reversed alpha blending, in LAB color space.
	*/
	get lab() {
		return this.overwriteGetter("lab", rgbToLab(this.rgb));
	}
	/**
	* Lazy getter pattern. When getter is called for the first time lazy value
	* is calculated and then overwrites getter function in given object instance.
	*
	* @example:
	* const redColor = Color.parse('red');
	* let x = redColor.hcl; // this will invoke `get hcl()`, which will calculate
	* // the value of red in HCL space and invoke this `overwriteGetter` function
	* // which in turn will set a field with a key 'hcl' in the `redColor` object.
	* // In other words it will override `get hcl()` from its `Color` prototype
	* // with its own property: hcl = [calculated red value in hcl].
	* let y = redColor.hcl; // next call will no longer invoke getter but simply
	* // return the previously calculated value
	* x === y; // true - `x` is exactly the same object as `y`
	*
	* @param getterKey Getter key
	* @param lazyValue Lazily calculated value to be memoized by current instance
	* @private
	*/
	overwriteGetter(getterKey, lazyValue) {
		Object.defineProperty(this, getterKey, { value: lazyValue });
		return lazyValue;
	}
	/**
	* Used by 'to-string' expression.
	*
	* @returns Serialized color in format `rgba(r,g,b,a)`
	* where r,g,b are numbers within 0..255 and alpha is number within 1..0
	*
	* @example
	* var purple = new Color.parse('purple');
	* purple.toString; // = "rgba(128,0,128,1)"
	* var translucentGreen = new Color.parse('rgba(26, 207, 26, .73)');
	* translucentGreen.toString(); // = "rgba(26,207,26,0.73)"
	*/
	toString() {
		const [r, g, b, a] = this.rgb;
		return `rgba(${[
			r,
			g,
			b
		].map((n) => Math.round(n * 255)).join(",")},${a})`;
	}
	static interpolate(from, to, t, spaceKey = "rgb") {
		switch (spaceKey) {
			case "rgb": {
				const [r, g, b, alpha] = interpolateArray(from.rgb, to.rgb, t);
				return new Color(r, g, b, alpha, false);
			}
			case "hcl": {
				const [hue0, chroma0, light0, alphaF] = from.hcl;
				const [hue1, chroma1, light1, alphaT] = to.hcl;
				let hue, chroma;
				if (!isNaN(hue0) && !isNaN(hue1)) {
					let dh = hue1 - hue0;
					if (hue1 > hue0 && dh > 180) dh -= 360;
					else if (hue1 < hue0 && hue0 - hue1 > 180) dh += 360;
					hue = hue0 + t * dh;
				} else if (!isNaN(hue0)) {
					hue = hue0;
					if (light1 === 1 || light1 === 0) chroma = chroma0;
				} else if (!isNaN(hue1)) {
					hue = hue1;
					if (light0 === 1 || light0 === 0) chroma = chroma1;
				} else hue = NaN;
				const [r, g, b, alpha] = hclToRgb([
					hue,
					chroma ?? interpolateNumber(chroma0, chroma1, t),
					interpolateNumber(light0, light1, t),
					interpolateNumber(alphaF, alphaT, t)
				]);
				return new Color(r, g, b, alpha, false);
			}
			case "lab": {
				const [r, g, b, alpha] = labToRgb(interpolateArray(from.lab, to.lab, t));
				return new Color(r, g, b, alpha, false);
			}
		}
	}
};
//#endregion
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
//#region src/expression/types/padding.ts
/**
* A set of four numbers representing padding around a box. Create instances from
* bare arrays or numeric values using the static method `Padding.parse`.
* @private
*/
var Padding = class Padding {
	constructor(values) {
		this.values = values.slice();
	}
	/**
	* Numeric padding values
	* @param input A padding value
	* @returns A `Padding` instance, or `undefined` if the input is not a valid padding value.
	*/
	static parse(input) {
		if (input instanceof Padding) return input;
		if (typeof input === "number") return new Padding([
			input,
			input,
			input,
			input
		]);
		if (!Array.isArray(input)) return;
		if (input.length < 1 || input.length > 4) return;
		for (const val of input) if (typeof val !== "number") return;
		switch (input.length) {
			case 1:
				input = [
					input[0],
					input[0],
					input[0],
					input[0]
				];
				break;
			case 2:
				input = [
					input[0],
					input[1],
					input[0],
					input[1]
				];
				break;
			case 3: input = [
				input[0],
				input[1],
				input[2],
				input[1]
			];
		}
		return new Padding(input);
	}
	toString() {
		return JSON.stringify(this.values);
	}
	static interpolate(from, to, t) {
		return new Padding(interpolateArray(from.values, to.values, t));
	}
};
//#endregion
//#region src/expression/types/number_array.ts
/**
* An array of numbers. Create instances from
* bare arrays or numeric values using the static method `NumberArray.parse`.
* @private
*/
var NumberArray = class NumberArray {
	constructor(values) {
		this.values = values.slice();
	}
	/**
	* Numeric NumberArray values
	* @param input A NumberArray value
	* @returns A `NumberArray` instance, or `undefined` if the input is not a valid NumberArray value.
	*/
	static parse(input) {
		if (input instanceof NumberArray) return input;
		if (typeof input === "number") return new NumberArray([input]);
		if (!Array.isArray(input)) return;
		for (const val of input) if (typeof val !== "number") return;
		return new NumberArray(input);
	}
	toString() {
		return JSON.stringify(this.values);
	}
	static interpolate(from, to, t) {
		return new NumberArray(interpolateArray(from.values, to.values, t));
	}
};
//#endregion
//#region src/expression/types/color_array.ts
/**
* An array of colors. Create instances from
* bare arrays or strings using the static method `ColorArray.parse`.
* @private
*/
var ColorArray = class ColorArray {
	constructor(values) {
		this.values = values.slice();
	}
	/**
	* ColorArray values
	* @param input A ColorArray value
	* @returns A `ColorArray` instance, or `undefined` if the input is not a valid ColorArray value.
	*/
	static parse(input) {
		if (input instanceof ColorArray) return input;
		if (typeof input === "string") {
			const parsed_val = Color.parse(input);
			if (!parsed_val) return;
			return new ColorArray([parsed_val]);
		}
		if (!Array.isArray(input)) return;
		const colors = [];
		for (const val of input) {
			if (typeof val !== "string") return;
			const parsed_val = Color.parse(val);
			if (!parsed_val) return;
			colors.push(parsed_val);
		}
		return new ColorArray(colors);
	}
	toString() {
		return JSON.stringify(this.values);
	}
	static interpolate(from, to, t, spaceKey = "rgb") {
		const colors = [];
		if (from.values.length != to.values.length) throw new Error(`colorArray: Arrays have mismatched length (${from.values.length} vs. ${to.values.length}), cannot interpolate.`);
		for (let i = 0; i < from.values.length; i++) colors.push(Color.interpolate(from.values[i], to.values[i], t, spaceKey));
		return new ColorArray(colors);
	}
};
//#endregion
//#region src/expression/runtime_error.ts
var RuntimeError = class extends Error {
	constructor(message, path) {
		super(message);
		this.name = "RuntimeError";
		this.path = path;
	}
	toJSON() {
		return this.message;
	}
};
//#endregion
//#region src/expression/types/variable_anchor_offset_collection.ts
/** Set of valid anchor positions, as a set for validation */
const anchors = /* @__PURE__ */ new Set([
	"center",
	"left",
	"right",
	"top",
	"bottom",
	"top-left",
	"top-right",
	"bottom-left",
	"bottom-right"
]);
/**
* Utility class to assist managing values for text-variable-anchor-offset property. Create instances from
* bare arrays using the static method `VariableAnchorOffsetCollection.parse`.
* @private
*/
var VariableAnchorOffsetCollection = class VariableAnchorOffsetCollection {
	constructor(values) {
		this.values = values.slice();
	}
	static parse(input) {
		if (input instanceof VariableAnchorOffsetCollection) return input;
		if (!Array.isArray(input) || input.length < 1 || input.length % 2 !== 0) return;
		for (let i = 0; i < input.length; i += 2) {
			const anchorValue = input[i];
			const offsetValue = input[i + 1];
			if (typeof anchorValue !== "string" || !anchors.has(anchorValue)) return;
			if (!Array.isArray(offsetValue) || offsetValue.length !== 2 || typeof offsetValue[0] !== "number" || typeof offsetValue[1] !== "number") return;
		}
		return new VariableAnchorOffsetCollection(input);
	}
	toString() {
		return JSON.stringify(this.values);
	}
	static interpolate(from, to, t, key) {
		const fromValues = from.values;
		const toValues = to.values;
		if (fromValues.length !== toValues.length) throw new RuntimeError(`Cannot interpolate values of different length. from: ${from.toString()}, to: ${to.toString()}`, key);
		const output = [];
		for (let i = 0; i < fromValues.length; i += 2) {
			if (fromValues[i] !== toValues[i]) throw new RuntimeError(`Cannot interpolate values containing mismatched anchors. from[${i}]: ${fromValues[i]}, to[${i}]: ${toValues[i]}`, key);
			output.push(fromValues[i]);
			const [fx, fy] = fromValues[i + 1];
			const [tx, ty] = toValues[i + 1];
			output.push([interpolateNumber(fx, tx, t), interpolateNumber(fy, ty, t)]);
		}
		return new VariableAnchorOffsetCollection(output);
	}
};
//#endregion
//#region src/expression/types/resolved_image.ts
var ResolvedImage = class ResolvedImage {
	constructor(options) {
		this.name = options.name;
		this.available = options.available;
	}
	toString() {
		return this.name;
	}
	static fromString(name) {
		if (!name) return null;
		return new ResolvedImage({
			name,
			available: false
		});
	}
};
//#endregion
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
//#region src/expression/values.ts
function validateRGBA(r, g, b, a) {
	if (!(typeof r === "number" && r >= 0 && r <= 255 && typeof g === "number" && g >= 0 && g <= 255 && typeof b === "number" && b >= 0 && b <= 255)) return `Invalid rgba value [${(typeof a === "number" ? [
		r,
		g,
		b,
		a
	] : [
		r,
		g,
		b
	]).join(", ")}]: 'r', 'g', and 'b' must be between 0 and 255.`;
	if (!(typeof a === "undefined" || typeof a === "number" && a >= 0 && a <= 1)) return `Invalid rgba value [${[
		r,
		g,
		b,
		a
	].join(", ")}]: 'a' must be between 0 and 1.`;
	return null;
}
function isValue(mixed) {
	if (mixed === null || typeof mixed === "string" || typeof mixed === "boolean" || typeof mixed === "number" || mixed instanceof ProjectionDefinition || mixed instanceof Color || mixed instanceof Collator || mixed instanceof Formatted || mixed instanceof Padding || mixed instanceof NumberArray || mixed instanceof ColorArray || mixed instanceof VariableAnchorOffsetCollection || mixed instanceof ResolvedImage) return true;
	else if (Array.isArray(mixed)) {
		for (const item of mixed) if (!isValue(item)) return false;
		return true;
	} else if (typeof mixed === "object") {
		for (const key in mixed) if (!isValue(mixed[key])) return false;
		return true;
	} else return false;
}
function typeOf(value) {
	if (value === null) return NullType;
	else if (typeof value === "string") return StringType;
	else if (typeof value === "boolean") return BooleanType;
	else if (typeof value === "number") return NumberType;
	else if (value instanceof Color) return ColorType;
	else if (value instanceof ProjectionDefinition) return ProjectionDefinitionType;
	else if (value instanceof Collator) return CollatorType;
	else if (value instanceof Formatted) return FormattedType;
	else if (value instanceof Padding) return PaddingType;
	else if (value instanceof NumberArray) return NumberArrayType;
	else if (value instanceof ColorArray) return ColorArrayType;
	else if (value instanceof VariableAnchorOffsetCollection) return VariableAnchorOffsetCollectionType;
	else if (value instanceof ResolvedImage) return ResolvedImageType;
	else if (Array.isArray(value)) {
		const length = value.length;
		let itemType;
		for (const item of value) {
			const t = typeOf(item);
			if (!itemType) itemType = t;
			else if (itemType === t) continue;
			else {
				itemType = ValueType;
				break;
			}
		}
		return array(itemType || ValueType, length);
	} else return ObjectType;
}
function valueToString(value) {
	const type = typeof value;
	if (value === null) return "";
	else if (type === "string" || type === "number" || type === "boolean") return String(value);
	else if (value instanceof Color || value instanceof ProjectionDefinition || value instanceof Formatted || value instanceof Padding || value instanceof NumberArray || value instanceof ColorArray || value instanceof VariableAnchorOffsetCollection || value instanceof ResolvedImage) return value.toString();
	else return JSON.stringify(value);
}
//#endregion
//#region src/expression/definitions/literal.ts
var Literal = class Literal {
	constructor(type, value) {
		this.type = type;
		this.value = value;
	}
	static parse(args, context) {
		if (args.length !== 2) return context.error(`'literal' expression requires exactly one argument, but found ${args.length - 1} instead.`);
		if (!isValue(args[1])) return context.error(`invalid value of type "${typeof args[1]}"`);
		const value = args[1];
		let type = typeOf(value);
		const expected = context.expectedType;
		if (type.kind === "array" && type.N === 0 && expected && expected.kind === "array" && (typeof expected.N !== "number" || expected.N === 0)) type = expected;
		return new Literal(type, value);
	}
	evaluate() {
		return this.value;
	}
	eachChild() {}
	outputDefined() {
		return true;
	}
};
//#endregion
//#region src/expression/definitions/assertion.ts
const types$1 = {
	string: StringType,
	number: NumberType,
	boolean: BooleanType,
	object: ObjectType
};
var Assertion = class Assertion {
	constructor(type, args, key) {
		this.type = type;
		this.args = args;
		this.key = key;
	}
	static parse(args, context) {
		if (args.length < 2) return context.error("Expected at least one argument.");
		let i = 1;
		let type;
		const name = args[0];
		if (name === "array") {
			let itemType;
			if (args.length > 2) {
				const type = args[1];
				if (typeof type !== "string" || !(type in types$1) || type === "object") return context.error("The item type argument of \"array\" must be one of string, number, boolean", 1);
				itemType = types$1[type];
				i++;
			} else itemType = ValueType;
			let N;
			if (args.length > 3) {
				if (args[2] !== null && (typeof args[2] !== "number" || args[2] < 0 || args[2] !== Math.floor(args[2]))) return context.error("The length argument to \"array\" must be a positive integer literal", 2);
				N = args[2];
				i++;
			}
			type = array(itemType, N);
		} else {
			if (!types$1[name]) throw new Error(`Types doesn't contain name = ${name}`);
			type = types$1[name];
		}
		const parsed = [];
		for (; i < args.length; i++) {
			const input = context.parse(args[i], i, ValueType);
			if (!input) return null;
			parsed.push(input);
		}
		return new Assertion(type, parsed, context.key);
	}
	evaluate(ctx) {
		for (let i = 0; i < this.args.length; i++) {
			const value = this.args[i].evaluate(ctx);
			if (!checkSubtype(this.type, typeOf(value))) return value;
			else if (i === this.args.length - 1) throw new RuntimeError(`Expected value to be of type ${typeToString(this.type)}, but found ${typeToString(typeOf(value))} instead.`, this.key);
		}
		throw new Error();
	}
	eachChild(fn) {
		this.args.forEach(fn);
	}
	outputDefined() {
		return this.args.every((arg) => arg.outputDefined());
	}
};
//#endregion
//#region src/expression/definitions/coercion.ts
const types = {
	"to-boolean": BooleanType,
	"to-color": ColorType,
	"to-number": NumberType,
	"to-string": StringType
};
/**
* Special form for error-coalescing coercion expressions "to-number",
* "to-color".  Since these coercions can fail at runtime, they accept multiple
* arguments, only evaluating one at a time until one succeeds.
*
* @private
*/
var Coercion = class Coercion {
	constructor(type, args, key) {
		this.type = type;
		this.args = args;
		this.key = key;
	}
	static parse(args, context) {
		if (args.length < 2) return context.error("Expected at least one argument.");
		const name = args[0];
		if (!types[name]) throw new Error(`Can't parse ${name} as it is not part of the known types`);
		if ((name === "to-boolean" || name === "to-string") && args.length !== 2) return context.error("Expected one argument.");
		const type = types[name];
		const parsed = [];
		for (let i = 1; i < args.length; i++) {
			const input = context.parse(args[i], i, ValueType);
			if (!input) return null;
			parsed.push(input);
		}
		return new Coercion(type, parsed, context.key);
	}
	evaluate(ctx) {
		switch (this.type.kind) {
			case "boolean": return Boolean(this.args[0].evaluate(ctx));
			case "color": {
				let input;
				let error;
				for (const arg of this.args) {
					input = arg.evaluate(ctx);
					error = null;
					if (input instanceof Color) return input;
					else if (typeof input === "string") {
						const c = ctx.parseColor(input);
						if (c) return c;
					} else if (Array.isArray(input)) {
						if (input.length < 3 || input.length > 4) error = `Invalid rgba value ${JSON.stringify(input)}: expected an array containing either three or four numeric values.`;
						else error = validateRGBA(input[0], input[1], input[2], input[3]);
						if (!error) return new Color(input[0] / 255, input[1] / 255, input[2] / 255, input[3]);
					}
				}
				throw new RuntimeError(error || `Could not parse color from value '${typeof input === "string" ? input : JSON.stringify(input)}'`, this.key);
			}
			case "padding": {
				let input;
				for (const arg of this.args) {
					input = arg.evaluate(ctx);
					const pad = Padding.parse(input);
					if (pad) return pad;
				}
				throw new RuntimeError(`Could not parse padding from value '${typeof input === "string" ? input : JSON.stringify(input)}'`, this.key);
			}
			case "numberArray": {
				let input;
				for (const arg of this.args) {
					input = arg.evaluate(ctx);
					const val = NumberArray.parse(input);
					if (val) return val;
				}
				throw new RuntimeError(`Could not parse numberArray from value '${typeof input === "string" ? input : JSON.stringify(input)}'`, this.key);
			}
			case "colorArray": {
				let input;
				for (const arg of this.args) {
					input = arg.evaluate(ctx);
					const val = ColorArray.parse(input);
					if (val) return val;
				}
				throw new RuntimeError(`Could not parse colorArray from value '${typeof input === "string" ? input : JSON.stringify(input)}'`, this.key);
			}
			case "variableAnchorOffsetCollection": {
				let input;
				for (const arg of this.args) {
					input = arg.evaluate(ctx);
					const coll = VariableAnchorOffsetCollection.parse(input);
					if (coll) return coll;
				}
				throw new RuntimeError(`Could not parse variableAnchorOffsetCollection from value '${typeof input === "string" ? input : JSON.stringify(input)}'`, this.key);
			}
			case "number": {
				let value = null;
				for (const arg of this.args) {
					value = arg.evaluate(ctx);
					if (value === null) return 0;
					const num = Number(value);
					if (isNaN(num)) continue;
					return num;
				}
				throw new RuntimeError(`Could not convert ${JSON.stringify(value)} to number.`, this.key);
			}
			case "formatted": return Formatted.fromString(valueToString(this.args[0].evaluate(ctx)));
			case "resolvedImage": return ResolvedImage.fromString(valueToString(this.args[0].evaluate(ctx)));
			case "projectionDefinition": {
				const input = this.args[0].evaluate(ctx);
				if (ProjectionDefinition.parse(input)) return input;
				throw new RuntimeError(`Could not parse projectionDefinition from value '${typeof input === "string" ? input : JSON.stringify(input)}'`, this.key);
			}
			default: return valueToString(this.args[0].evaluate(ctx));
		}
	}
	eachChild(fn) {
		this.args.forEach(fn);
	}
	outputDefined() {
		return this.args.every((arg) => arg.outputDefined());
	}
};
//#endregion
//#region src/expression/definitions/let.ts
var Let = class Let {
	constructor(bindings, result) {
		this.type = result.type;
		this.bindings = [].concat(bindings);
		this.result = result;
	}
	evaluate(ctx) {
		return this.result.evaluate(ctx);
	}
	eachChild(fn) {
		for (const binding of this.bindings) fn(binding[1]);
		fn(this.result);
	}
	static parse(args, context) {
		if (args.length < 4) return context.error(`Expected at least 3 arguments, but found ${args.length - 1} instead.`);
		const bindings = [];
		for (let i = 1; i < args.length - 1; i += 2) {
			const name = args[i];
			if (typeof name !== "string") return context.error(`Expected string, but found ${typeof name} instead.`, i);
			if (/[^a-zA-Z0-9_]/.test(name)) return context.error("Variable names must contain only alphanumeric characters or '_'.", i);
			const value = context.parse(args[i + 1], i + 1);
			if (!value) return null;
			bindings.push([name, value]);
		}
		const result = context.parse(args[args.length - 1], args.length - 1, context.expectedType, bindings);
		if (!result) return null;
		return new Let(bindings, result);
	}
	outputDefined() {
		return this.result.outputDefined();
	}
};
//#endregion
//#region src/expression/definitions/var.ts
var Var = class Var {
	constructor(name, boundExpression) {
		this.type = boundExpression.type;
		this.name = name;
		this.boundExpression = boundExpression;
	}
	static parse(args, context) {
		if (args.length !== 2 || typeof args[1] !== "string") return context.error("'var' expression requires exactly one string literal argument.");
		const name = args[1];
		if (!context.scope.has(name)) return context.error(`Unknown variable "${name}". Make sure "${name}" has been bound in an enclosing "let" expression before using it.`, 1);
		return new Var(name, context.scope.get(name));
	}
	evaluate(ctx) {
		return this.boundExpression.evaluate(ctx);
	}
	eachChild() {}
	outputDefined() {
		return false;
	}
};
//#endregion
//#region src/expression/definitions/at.ts
var At = class At {
	constructor(type, index, input, key) {
		this.type = type;
		this.index = index;
		this.input = input;
		this.key = key;
	}
	static parse(args, context) {
		if (args.length !== 3) return context.error(`Expected 2 arguments, but found ${args.length - 1} instead.`);
		const index = context.parse(args[1], 1, NumberType);
		const input = context.parse(args[2], 2, array(context.expectedType || ValueType));
		if (!index || !input) return null;
		const t = input.type;
		return new At(t.itemType, index, input, context.key);
	}
	evaluate(ctx) {
		const index = this.index.evaluate(ctx);
		const array = this.input.evaluate(ctx);
		if (index < 0) throw new RuntimeError(`Array index out of bounds: ${index} < 0.`, this.key);
		if (index >= array.length) throw new RuntimeError(`Array index out of bounds: ${index} > ${array.length - 1}.`, this.key);
		if (index !== Math.floor(index)) throw new RuntimeError(`Array index must be an integer, but found ${index} instead.`, this.key);
		return array[index];
	}
	eachChild(fn) {
		fn(this.index);
		fn(this.input);
	}
	outputDefined() {
		return false;
	}
};
//#endregion
//#region src/expression/definitions/in.ts
var In = class In {
	constructor(needle, haystack, key) {
		this.needle = needle;
		this.haystack = haystack;
		this.key = key;
		this.type = BooleanType;
	}
	static parse(args, context) {
		if (args.length !== 3) return context.error(`Expected 2 arguments, but found ${args.length - 1} instead.`);
		const needle = context.parse(args[1], 1, ValueType);
		const haystack = context.parse(args[2], 2, ValueType);
		if (!needle || !haystack) return null;
		if (!isValidType(needle.type, [
			BooleanType,
			StringType,
			NumberType,
			NullType,
			ValueType
		])) return context.error(`Expected first argument to be of type boolean, string, number or null, but found ${typeToString(needle.type)} instead`);
		return new In(needle, haystack, context.key);
	}
	evaluate(ctx) {
		const needle = this.needle.evaluate(ctx);
		const haystack = this.haystack.evaluate(ctx);
		if (!haystack) return false;
		if (!isValidNativeType(needle, [
			"boolean",
			"string",
			"number",
			"null"
		])) throw new RuntimeError(`Expected first argument to be of type boolean, string, number or null, but found ${typeToString(typeOf(needle))} instead.`, this.key);
		if (!isValidNativeType(haystack, ["string", "array"])) throw new RuntimeError(`Expected second argument to be of type array or string, but found ${typeToString(typeOf(haystack))} instead.`, this.key);
		return haystack.indexOf(needle) >= 0;
	}
	eachChild(fn) {
		fn(this.needle);
		fn(this.haystack);
	}
	outputDefined() {
		return true;
	}
};
//#endregion
//#region src/expression/definitions/index_of.ts
var IndexOf = class IndexOf {
	constructor(needle, haystack, key, fromIndex) {
		this.needle = needle;
		this.haystack = haystack;
		this.key = key;
		this.fromIndex = fromIndex;
		this.type = NumberType;
	}
	static parse(args, context) {
		if (args.length <= 2 || args.length >= 5) return context.error(`Expected 2 or 3 arguments, but found ${args.length - 1} instead.`);
		const needle = context.parse(args[1], 1, ValueType);
		const haystack = context.parse(args[2], 2, ValueType);
		if (!needle || !haystack) return null;
		if (!isValidType(needle.type, [
			BooleanType,
			StringType,
			NumberType,
			NullType,
			ValueType
		])) return context.error(`Expected first argument to be of type boolean, string, number or null, but found ${typeToString(needle.type)} instead`);
		if (args.length === 4) {
			const fromIndex = context.parse(args[3], 3, NumberType);
			if (!fromIndex) return null;
			return new IndexOf(needle, haystack, context.key, fromIndex);
		} else return new IndexOf(needle, haystack, context.key);
	}
	evaluate(ctx) {
		const needle = this.needle.evaluate(ctx);
		const haystack = this.haystack.evaluate(ctx);
		if (!isValidNativeType(needle, [
			"boolean",
			"string",
			"number",
			"null"
		])) throw new RuntimeError(`Expected first argument to be of type boolean, string, number or null, but found ${typeToString(typeOf(needle))} instead.`, this.key);
		let fromIndex;
		if (this.fromIndex) fromIndex = this.fromIndex.evaluate(ctx);
		if (isValidNativeType(haystack, ["string"])) {
			const rawIndex = haystack.indexOf(needle, fromIndex);
			if (rawIndex === -1) return -1;
			else return [...haystack.slice(0, rawIndex)].length;
		} else if (isValidNativeType(haystack, ["array"])) return haystack.indexOf(needle, fromIndex);
		else throw new RuntimeError(`Expected second argument to be of type array or string, but found ${typeToString(typeOf(haystack))} instead.`, this.key);
	}
	eachChild(fn) {
		fn(this.needle);
		fn(this.haystack);
		if (this.fromIndex) fn(this.fromIndex);
	}
	outputDefined() {
		return false;
	}
};
//#endregion
//#region src/expression/definitions/match.ts
var Match = class Match {
	constructor(inputType, outputType, input, cases, outputs, otherwise) {
		this.inputType = inputType;
		this.type = outputType;
		this.input = input;
		this.cases = cases;
		this.outputs = outputs;
		this.otherwise = otherwise;
	}
	static parse(args, context) {
		if (args.length < 5) return context.error(`Expected at least 4 arguments, but found only ${args.length - 1}.`);
		if (args.length % 2 !== 1) return context.error("Expected an even number of arguments.");
		let inputType;
		let outputType;
		if (context.expectedType && context.expectedType.kind !== "value") outputType = context.expectedType;
		const cases = {};
		const outputs = [];
		for (let i = 2; i < args.length - 1; i += 2) {
			let labels = args[i];
			const value = args[i + 1];
			if (!Array.isArray(labels)) labels = [labels];
			const labelContext = context.concat(i);
			if (labels.length === 0) return labelContext.error("Expected at least one branch label.");
			for (const label of labels) {
				if (typeof label !== "number" && typeof label !== "string") return labelContext.error("Branch labels must be numbers or strings.");
				else if (typeof label === "number" && Math.abs(label) > Number.MAX_SAFE_INTEGER) return labelContext.error(`Branch labels must be integers no larger than ${Number.MAX_SAFE_INTEGER}.`);
				else if (typeof label === "number" && Math.floor(label) !== label) return labelContext.error("Numeric branch labels must be integer values.");
				else if (!inputType) inputType = typeOf(label);
				else if (labelContext.checkSubtype(inputType, typeOf(label))) return null;
				if (typeof cases[String(label)] !== "undefined") return labelContext.error("Branch labels must be unique.");
				cases[String(label)] = outputs.length;
			}
			const result = context.parse(value, i, outputType);
			if (!result) return null;
			outputType = outputType || result.type;
			outputs.push(result);
		}
		const input = context.parse(args[1], 1, ValueType);
		if (!input) return null;
		const otherwise = context.parse(args[args.length - 1], args.length - 1, outputType);
		if (!otherwise) return null;
		if (input.type.kind !== "value" && context.concat(1).checkSubtype(inputType, input.type)) return null;
		return new Match(inputType, outputType, input, cases, outputs, otherwise);
	}
	evaluate(ctx) {
		const input = this.input.evaluate(ctx);
		return (typeOf(input) === this.inputType && this.outputs[this.cases[input]] || this.otherwise).evaluate(ctx);
	}
	eachChild(fn) {
		fn(this.input);
		this.outputs.forEach(fn);
		fn(this.otherwise);
	}
	outputDefined() {
		return this.outputs.every((out) => out.outputDefined()) && this.otherwise.outputDefined();
	}
};
//#endregion
//#region src/expression/definitions/case.ts
var Case = class Case {
	constructor(type, branches, otherwise) {
		this.type = type;
		this.branches = branches;
		this.otherwise = otherwise;
	}
	static parse(args, context) {
		if (args.length < 4) return context.error(`Expected at least 3 arguments, but found only ${args.length - 1}.`);
		if (args.length % 2 !== 0) return context.error("Expected an odd number of arguments.");
		let outputType;
		if (context.expectedType && context.expectedType.kind !== "value") outputType = context.expectedType;
		const branches = [];
		for (let i = 1; i < args.length - 1; i += 2) {
			const test = context.parse(args[i], i, BooleanType);
			if (!test) return null;
			const result = context.parse(args[i + 1], i + 1, outputType);
			if (!result) return null;
			branches.push([test, result]);
			outputType = outputType || result.type;
		}
		const otherwise = context.parse(args[args.length - 1], args.length - 1, outputType);
		if (!otherwise) return null;
		if (!outputType) throw new Error("Can't infer output type");
		return new Case(outputType, branches, otherwise);
	}
	evaluate(ctx) {
		for (const [test, expression] of this.branches) if (test.evaluate(ctx)) return expression.evaluate(ctx);
		return this.otherwise.evaluate(ctx);
	}
	eachChild(fn) {
		for (const [test, expression] of this.branches) {
			fn(test);
			fn(expression);
		}
		fn(this.otherwise);
	}
	outputDefined() {
		return this.branches.every(([_, out]) => out.outputDefined()) && this.otherwise.outputDefined();
	}
};
//#endregion
//#region src/expression/definitions/slice.ts
var Slice = class Slice {
	constructor(type, input, beginIndex, key, endIndex) {
		this.type = type;
		this.input = input;
		this.beginIndex = beginIndex;
		this.key = key;
		this.endIndex = endIndex;
	}
	static parse(args, context) {
		if (args.length <= 2 || args.length >= 5) return context.error(`Expected 2 or 3 arguments, but found ${args.length - 1} instead.`);
		const input = context.parse(args[1], 1, ValueType);
		const beginIndex = context.parse(args[2], 2, NumberType);
		if (!input || !beginIndex) return null;
		if (!isValidType(input.type, [
			array(ValueType),
			StringType,
			ValueType
		])) return context.error(`Expected first argument to be of type array or string, but found ${typeToString(input.type)} instead`);
		if (args.length === 4) {
			const endIndex = context.parse(args[3], 3, NumberType);
			if (!endIndex) return null;
			return new Slice(input.type, input, beginIndex, context.key, endIndex);
		} else return new Slice(input.type, input, beginIndex, context.key);
	}
	evaluate(ctx) {
		const input = this.input.evaluate(ctx);
		const beginIndex = this.beginIndex.evaluate(ctx);
		let endIndex;
		if (this.endIndex) endIndex = this.endIndex.evaluate(ctx);
		if (isValidNativeType(input, ["string"])) return [...input].slice(beginIndex, endIndex).join("");
		else if (isValidNativeType(input, ["array"])) return input.slice(beginIndex, endIndex);
		else throw new RuntimeError(`Expected first argument to be of type array or string, but found ${typeToString(typeOf(input))} instead.`, this.key);
	}
	eachChild(fn) {
		fn(this.input);
		fn(this.beginIndex);
		if (this.endIndex) fn(this.endIndex);
	}
	outputDefined() {
		return false;
	}
};
//#endregion
//#region src/expression/stops.ts
/**
* Returns the index of the last stop <= input, or 0 if it doesn't exist.
* @private
*/
function findStopLessThanOrEqualTo(stops, input, key) {
	const lastIndex = stops.length - 1;
	let lowerIndex = 0;
	let upperIndex = lastIndex;
	let currentIndex = 0;
	let currentValue, nextValue;
	while (lowerIndex <= upperIndex) {
		currentIndex = Math.floor((lowerIndex + upperIndex) / 2);
		currentValue = stops[currentIndex];
		nextValue = stops[currentIndex + 1];
		if (currentValue <= input) {
			if (currentIndex === lastIndex || input < nextValue) return currentIndex;
			lowerIndex = currentIndex + 1;
		} else if (currentValue > input) upperIndex = currentIndex - 1;
		else throw new RuntimeError("Input is not a number.", key);
	}
	return 0;
}
//#endregion
//#region src/expression/definitions/step.ts
var Step = class Step {
	constructor(type, input, stops, key) {
		this.type = type;
		this.input = input;
		this.key = key;
		this.labels = [];
		this.outputs = [];
		for (const [label, expression] of stops) {
			this.labels.push(label);
			this.outputs.push(expression);
		}
	}
	static parse(args, context) {
		if (args.length - 1 < 4) return context.error(`Expected at least 4 arguments, but found only ${args.length - 1}.`);
		if ((args.length - 1) % 2 !== 0) return context.error("Expected an even number of arguments.");
		const input = context.parse(args[1], 1, NumberType);
		if (!input) return null;
		const stops = [];
		let outputType = null;
		if (context.expectedType && context.expectedType.kind !== "value") outputType = context.expectedType;
		for (let i = 1; i < args.length; i += 2) {
			const label = i === 1 ? -Infinity : args[i];
			const value = args[i + 1];
			const labelKey = i;
			const valueKey = i + 1;
			if (typeof label !== "number") return context.error("Input/output pairs for \"step\" expressions must be defined using literal numeric values (not computed expressions) for the input values.", labelKey);
			if (stops.length && stops[stops.length - 1][0] >= label) return context.error("Input/output pairs for \"step\" expressions must be arranged with input values in strictly ascending order.", labelKey);
			const parsed = context.parse(value, valueKey, outputType);
			if (!parsed) return null;
			outputType = outputType || parsed.type;
			stops.push([label, parsed]);
		}
		return new Step(outputType, input, stops, context.key);
	}
	evaluate(ctx) {
		const labels = this.labels;
		const outputs = this.outputs;
		if (labels.length === 1) return outputs[0].evaluate(ctx);
		const value = this.input.evaluate(ctx);
		if (value <= labels[0]) return outputs[0].evaluate(ctx);
		const stopCount = labels.length;
		if (value >= labels[stopCount - 1]) return outputs[stopCount - 1].evaluate(ctx);
		return outputs[findStopLessThanOrEqualTo(labels, value, this.key)].evaluate(ctx);
	}
	eachChild(fn) {
		fn(this.input);
		for (const expression of this.outputs) fn(expression);
	}
	outputDefined() {
		return this.outputs.every((out) => out.outputDefined());
	}
};
//#endregion
//#region node_modules/@mapbox/unitbezier/index.js
function unitBezier(p1x, p1y, p2x, p2y) {
	const cx = 3 * p1x;
	const bx = 3 * (p2x - p1x) - cx;
	const ax = 1 - cx - bx;
	const cy = 3 * p1y;
	const by = 3 * (p2y - p1y) - cy;
	const ay = 1 - cy - by;
	return function solve(x, epsilon = 1e-6) {
		if (x <= 0) return 0;
		if (x >= 1) return 1;
		let t = x;
		for (let i = 0; i < 8; i++) {
			const x2 = ((ax * t + bx) * t + cx) * t - x;
			if (Math.abs(x2) < epsilon) return ((ay * t + by) * t + cy) * t;
			const d2 = (3 * ax * t + 2 * bx) * t + cx;
			if (Math.abs(d2) < 1e-6) break;
			t -= x2 / d2;
		}
		let t0 = 0;
		let t1 = 1;
		t = x;
		for (let i = 0; i < 20; i++) {
			const x2 = ((ax * t + bx) * t + cx) * t;
			if (Math.abs(x2 - x) < epsilon) break;
			if (x > x2) t0 = t;
			else t1 = t;
			t = (t0 + t1) * .5;
		}
		return ((ay * t + by) * t + cy) * t;
	};
}
//#endregion
//#region src/expression/definitions/interpolate.ts
var Interpolate = class Interpolate {
	constructor(type, operator, interpolation, input, stops, key) {
		this.type = type;
		this.operator = operator;
		this.interpolation = interpolation;
		this.input = input;
		this.key = key;
		this.labels = [];
		this.outputs = [];
		for (const [label, expression] of stops) {
			this.labels.push(label);
			this.outputs.push(expression);
		}
	}
	static interpolationFactor(interpolation, input, lower, upper) {
		let t = 0;
		if (interpolation.name === "exponential") t = exponentialInterpolation(input, interpolation.base, lower, upper);
		else if (interpolation.name === "linear") t = exponentialInterpolation(input, 1, lower, upper);
		else if (interpolation.name === "cubic-bezier") {
			const c = interpolation.controlPoints;
			t = unitBezier(c[0], c[1], c[2], c[3])(exponentialInterpolation(input, 1, lower, upper));
		}
		return t;
	}
	static parse(args, context) {
		let [operator, interpolation, input, ...rest] = args;
		if (!Array.isArray(interpolation) || interpolation.length === 0) return context.error("Expected an interpolation type expression.", 1);
		if (interpolation[0] === "linear") interpolation = { name: "linear" };
		else if (interpolation[0] === "exponential") {
			const base = interpolation[1];
			if (typeof base !== "number") return context.error("Exponential interpolation requires a numeric base.", 1, 1);
			interpolation = {
				name: "exponential",
				base
			};
		} else if (interpolation[0] === "cubic-bezier") {
			const controlPoints = interpolation.slice(1);
			if (controlPoints.length !== 4 || controlPoints.some((t) => typeof t !== "number" || t < 0 || t > 1)) return context.error("Cubic bezier interpolation requires four numeric arguments with values between 0 and 1.", 1);
			interpolation = {
				name: "cubic-bezier",
				controlPoints
			};
		} else return context.error(`Unknown interpolation type ${String(interpolation[0])}`, 1, 0);
		if (args.length - 1 < 4) return context.error(`Expected at least 4 arguments, but found only ${args.length - 1}.`);
		if ((args.length - 1) % 2 !== 0) return context.error("Expected an even number of arguments.");
		input = context.parse(input, 2, NumberType);
		if (!input) return null;
		const stops = [];
		let outputType = null;
		if ((operator === "interpolate-hcl" || operator === "interpolate-lab") && context.expectedType != ColorArrayType) outputType = ColorType;
		else if (context.expectedType && context.expectedType.kind !== "value") outputType = context.expectedType;
		for (let i = 0; i < rest.length; i += 2) {
			const label = rest[i];
			const value = rest[i + 1];
			const labelKey = i + 3;
			const valueKey = i + 4;
			if (typeof label !== "number") return context.error("Input/output pairs for \"interpolate\" expressions must be defined using literal numeric values (not computed expressions) for the input values.", labelKey);
			if (stops.length && stops[stops.length - 1][0] >= label) return context.error("Input/output pairs for \"interpolate\" expressions must be arranged with input values in strictly ascending order.", labelKey);
			const parsed = context.parse(value, valueKey, outputType);
			if (!parsed) return null;
			outputType = outputType || parsed.type;
			stops.push([label, parsed]);
		}
		if (!verifyType(outputType, NumberType) && !verifyType(outputType, ProjectionDefinitionType) && !verifyType(outputType, ColorType) && !verifyType(outputType, PaddingType) && !verifyType(outputType, NumberArrayType) && !verifyType(outputType, ColorArrayType) && !verifyType(outputType, VariableAnchorOffsetCollectionType) && !verifyType(outputType, array(NumberType))) return context.error(`Type ${typeToString(outputType)} is not interpolatable.`);
		return new Interpolate(outputType, operator, interpolation, input, stops, context.key);
	}
	evaluate(ctx) {
		const labels = this.labels;
		const outputs = this.outputs;
		if (labels.length === 1) return outputs[0].evaluate(ctx);
		const value = this.input.evaluate(ctx);
		if (value <= labels[0]) return outputs[0].evaluate(ctx);
		const stopCount = labels.length;
		if (value >= labels[stopCount - 1]) return outputs[stopCount - 1].evaluate(ctx);
		const index = findStopLessThanOrEqualTo(labels, value, this.key);
		const lower = labels[index];
		const upper = labels[index + 1];
		const t = Interpolate.interpolationFactor(this.interpolation, value, lower, upper);
		const outputLower = outputs[index].evaluate(ctx);
		const outputUpper = outputs[index + 1].evaluate(ctx);
		switch (this.operator) {
			case "interpolate": switch (this.type.kind) {
				case "number": return interpolateNumber(outputLower, outputUpper, t);
				case "color": return Color.interpolate(outputLower, outputUpper, t);
				case "padding": return Padding.interpolate(outputLower, outputUpper, t);
				case "colorArray": return ColorArray.interpolate(outputLower, outputUpper, t);
				case "numberArray": return NumberArray.interpolate(outputLower, outputUpper, t);
				case "variableAnchorOffsetCollection": return VariableAnchorOffsetCollection.interpolate(outputLower, outputUpper, t, this.key);
				case "array": return interpolateArray(outputLower, outputUpper, t);
				case "projectionDefinition": return ProjectionDefinition.interpolate(outputLower, outputUpper, t);
			}
			case "interpolate-hcl": switch (this.type.kind) {
				case "color": return Color.interpolate(outputLower, outputUpper, t, "hcl");
				case "colorArray": return ColorArray.interpolate(outputLower, outputUpper, t, "hcl");
			}
			case "interpolate-lab": switch (this.type.kind) {
				case "color": return Color.interpolate(outputLower, outputUpper, t, "lab");
				case "colorArray": return ColorArray.interpolate(outputLower, outputUpper, t, "lab");
			}
		}
	}
	eachChild(fn) {
		fn(this.input);
		for (const expression of this.outputs) fn(expression);
	}
	outputDefined() {
		return this.outputs.every((out) => out.outputDefined());
	}
};
/**
* Returns a ratio that can be used to interpolate between exponential function
* stops.
* How it works: Two consecutive stop values define a (scaled and shifted) exponential function `f(x) = a * base^x + b`, where `base` is the user-specified base,
* and `a` and `b` are constants affording sufficient degrees of freedom to fit
* the function to the given stops.
*
* Here's a bit of algebra that lets us compute `f(x)` directly from the stop
* values without explicitly solving for `a` and `b`:
*
* First stop value: `f(x0) = y0 = a * base^x0 + b`
* Second stop value: `f(x1) = y1 = a * base^x1 + b`
* => `y1 - y0 = a(base^x1 - base^x0)`
* => `a = (y1 - y0)/(base^x1 - base^x0)`
*
* Desired value: `f(x) = y = a * base^x + b`
* => `f(x) = y0 + a * (base^x - base^x0)`
*
* From the above, we can replace the `a` in `a * (base^x - base^x0)` and do a
* little algebra:
* ```
* a * (base^x - base^x0) = (y1 - y0)/(base^x1 - base^x0) * (base^x - base^x0)
*                     = (y1 - y0) * (base^x - base^x0) / (base^x1 - base^x0)
* ```
*
* If we let `(base^x - base^x0) / (base^x1 base^x0)`, then we have
* `f(x) = y0 + (y1 - y0) * ratio`.  In other words, `ratio` may be treated as
* an interpolation factor between the two stops' output values.
*
* (Note: a slightly different form for `ratio`,
* `(base^(x-x0) - 1) / (base^(x1-x0) - 1) `, is equivalent, but requires fewer
* expensive `Math.pow()` operations.)
*
* @private
*/
function exponentialInterpolation(input, base, lowerValue, upperValue) {
	const difference = upperValue - lowerValue;
	const progress = input - lowerValue;
	if (difference === 0) return 0;
	else if (base === 1) return progress / difference;
	else return (Math.pow(base, progress) - 1) / (Math.pow(base, difference) - 1);
}
Color.interpolate, Padding.interpolate, NumberArray.interpolate, ColorArray.interpolate, VariableAnchorOffsetCollection.interpolate;
//#endregion
//#region src/expression/definitions/coalesce.ts
var Coalesce = class Coalesce {
	constructor(type, args) {
		this.type = type;
		this.args = args;
	}
	static parse(args, context) {
		if (args.length < 2) return context.error("Expected at least one argument.");
		let outputType = null;
		const expectedType = context.expectedType;
		if (expectedType && expectedType.kind !== "value") outputType = expectedType;
		const parsedArgs = [];
		for (const arg of args.slice(1)) {
			const parsed = context.parse(arg, 1 + parsedArgs.length, outputType, void 0, { typeAnnotation: "omit" });
			if (!parsed) return null;
			outputType = outputType || parsed.type;
			parsedArgs.push(parsed);
		}
		if (!outputType) throw new Error("No output type");
		return expectedType && parsedArgs.some((arg) => checkSubtype(expectedType, arg.type)) ? new Coalesce(ValueType, parsedArgs) : new Coalesce(outputType, parsedArgs);
	}
	evaluate(ctx) {
		let result = null;
		let argCount = 0;
		let requestedImageName;
		for (const arg of this.args) {
			argCount++;
			result = arg.evaluate(ctx);
			if (result && result instanceof ResolvedImage && !result.available) {
				if (!requestedImageName) requestedImageName = result.name;
				result = null;
				if (argCount === this.args.length) result = requestedImageName;
			}
			if (result !== null) break;
		}
		return result;
	}
	eachChild(fn) {
		this.args.forEach(fn);
	}
	outputDefined() {
		return this.args.every((arg) => arg.outputDefined());
	}
};
//#endregion
//#region src/expression/definitions/comparison.ts
function isComparableType(op, type) {
	if (op === "==" || op === "!=") return type.kind === "boolean" || type.kind === "string" || type.kind === "number" || type.kind === "null" || type.kind === "value";
	else return type.kind === "string" || type.kind === "number" || type.kind === "value";
}
function eq(ctx, a, b) {
	return a === b;
}
function neq(ctx, a, b) {
	return a !== b;
}
function lt(ctx, a, b) {
	return a < b;
}
function gt(ctx, a, b) {
	return a > b;
}
function lteq(ctx, a, b) {
	return a <= b;
}
function gteq(ctx, a, b) {
	return a >= b;
}
function eqCollate(ctx, a, b, c) {
	return c.compare(a, b) === 0;
}
function neqCollate(ctx, a, b, c) {
	return !eqCollate(ctx, a, b, c);
}
function ltCollate(ctx, a, b, c) {
	return c.compare(a, b) < 0;
}
function gtCollate(ctx, a, b, c) {
	return c.compare(a, b) > 0;
}
function lteqCollate(ctx, a, b, c) {
	return c.compare(a, b) <= 0;
}
function gteqCollate(ctx, a, b, c) {
	return c.compare(a, b) >= 0;
}
/**
* Special form for comparison operators, implementing the signatures:
* - (T, T, ?Collator) => boolean
* - (T, value, ?Collator) => boolean
* - (value, T, ?Collator) => boolean
*
* For inequalities, T must be either value, string, or number. For ==/!=, it
* can also be boolean or null.
*
* Equality semantics are equivalent to Javascript's strict equality (===/!==)
* -- i.e., when the arguments' types don't match, == evaluates to false, != to
* true.
*
* When types don't match in an ordering comparison, a runtime error is thrown.
*
* @private
*/
function makeComparison(op, compareBasic, compareWithCollator) {
	const isOrderComparison = op !== "==" && op !== "!=";
	return class Comparison {
		constructor(lhs, rhs, key, collator) {
			this.lhs = lhs;
			this.rhs = rhs;
			this.key = key;
			this.collator = collator;
			this.type = BooleanType;
			this.hasUntypedArgument = lhs.type.kind === "value" || rhs.type.kind === "value";
		}
		static parse(args, context) {
			if (args.length !== 3 && args.length !== 4) return context.error("Expected two or three arguments.");
			const op = args[0];
			let lhs = context.parse(args[1], 1, ValueType);
			if (!lhs) return null;
			if (!isComparableType(op, lhs.type)) return context.concat(1).error(`"${op}" comparisons are not supported for type '${typeToString(lhs.type)}'.`);
			let rhs = context.parse(args[2], 2, ValueType);
			if (!rhs) return null;
			if (!isComparableType(op, rhs.type)) return context.concat(2).error(`"${op}" comparisons are not supported for type '${typeToString(rhs.type)}'.`);
			if (lhs.type.kind !== rhs.type.kind && lhs.type.kind !== "value" && rhs.type.kind !== "value") return context.error(`Cannot compare types '${typeToString(lhs.type)}' and '${typeToString(rhs.type)}'.`);
			if (isOrderComparison) {
				if (lhs.type.kind === "value" && rhs.type.kind !== "value") lhs = new Assertion(rhs.type, [lhs], context.key);
				else if (lhs.type.kind !== "value" && rhs.type.kind === "value") rhs = new Assertion(lhs.type, [rhs], context.key);
			}
			let collator = null;
			if (args.length === 4) {
				if (lhs.type.kind !== "string" && rhs.type.kind !== "string" && lhs.type.kind !== "value" && rhs.type.kind !== "value") return context.error("Cannot use collator to compare non-string types.");
				collator = context.parse(args[3], 3, CollatorType);
				if (!collator) return null;
			}
			return new Comparison(lhs, rhs, context.key, collator);
		}
		evaluate(ctx) {
			const lhs = this.lhs.evaluate(ctx);
			const rhs = this.rhs.evaluate(ctx);
			if (isOrderComparison && this.hasUntypedArgument) {
				const lt = typeOf(lhs);
				const rt = typeOf(rhs);
				if (lt.kind !== rt.kind || !(lt.kind === "string" || lt.kind === "number")) throw new RuntimeError(`Expected arguments for "${op}" to be (string, string) or (number, number), but found (${lt.kind}, ${rt.kind}) instead.`, this.key);
			}
			if (this.collator && !isOrderComparison && this.hasUntypedArgument) {
				const lt = typeOf(lhs);
				const rt = typeOf(rhs);
				if (lt.kind !== "string" || rt.kind !== "string") return compareBasic(ctx, lhs, rhs);
			}
			return this.collator ? compareWithCollator(ctx, lhs, rhs, this.collator.evaluate(ctx)) : compareBasic(ctx, lhs, rhs);
		}
		eachChild(fn) {
			fn(this.lhs);
			fn(this.rhs);
			if (this.collator) fn(this.collator);
		}
		outputDefined() {
			return true;
		}
	};
}
const Equals = makeComparison("==", eq, eqCollate);
const NotEquals = makeComparison("!=", neq, neqCollate);
const LessThan = makeComparison("<", lt, ltCollate);
const GreaterThan = makeComparison(">", gt, gtCollate);
const LessThanOrEqual = makeComparison("<=", lteq, lteqCollate);
const GreaterThanOrEqual = makeComparison(">=", gteq, gteqCollate);
//#endregion
//#region src/expression/definitions/collator.ts
var CollatorExpression = class CollatorExpression {
	constructor(caseSensitive, diacriticSensitive, locale) {
		this.type = CollatorType;
		this.locale = locale;
		this.caseSensitive = caseSensitive;
		this.diacriticSensitive = diacriticSensitive;
	}
	static parse(args, context) {
		if (args.length !== 2) return context.error("Expected one argument.");
		const options = args[1];
		if (typeof options !== "object" || Array.isArray(options)) return context.error("Collator options argument must be an object.");
		const caseSensitive = context.parse(options["case-sensitive"] === void 0 ? false : options["case-sensitive"], 1, BooleanType);
		if (!caseSensitive) return null;
		const diacriticSensitive = context.parse(options["diacritic-sensitive"] === void 0 ? false : options["diacritic-sensitive"], 1, BooleanType);
		if (!diacriticSensitive) return null;
		let locale = null;
		if (options["locale"]) {
			locale = context.parse(options["locale"], 1, StringType);
			if (!locale) return null;
		}
		return new CollatorExpression(caseSensitive, diacriticSensitive, locale);
	}
	evaluate(ctx) {
		return new Collator(this.caseSensitive.evaluate(ctx), this.diacriticSensitive.evaluate(ctx), this.locale ? this.locale.evaluate(ctx) : null);
	}
	eachChild(fn) {
		fn(this.caseSensitive);
		fn(this.diacriticSensitive);
		if (this.locale) fn(this.locale);
	}
	outputDefined() {
		return false;
	}
};
//#endregion
//#region src/expression/definitions/number_format.ts
var NumberFormat = class NumberFormat {
	constructor(number, locale, currency, unit, minFractionDigits, maxFractionDigits) {
		this.type = StringType;
		this.number = number;
		this.locale = locale;
		this.currency = currency;
		this.unit = unit;
		this.minFractionDigits = minFractionDigits;
		this.maxFractionDigits = maxFractionDigits;
	}
	static parse(args, context) {
		if (args.length !== 3) return context.error("Expected two arguments.");
		const number = context.parse(args[1], 1, NumberType);
		if (!number) return null;
		const options = args[2];
		if (typeof options !== "object" || Array.isArray(options)) return context.error("NumberFormat options argument must be an object.");
		let locale = null;
		if (options["locale"]) {
			locale = context.parse(options["locale"], 1, StringType);
			if (!locale) return null;
		}
		let currency = null;
		if (options["currency"]) {
			currency = context.parse(options["currency"], 1, StringType);
			if (!currency) return null;
		}
		let unit = null;
		if (options["unit"]) {
			unit = context.parse(options["unit"], 1, StringType);
			if (!unit) return null;
		}
		if (currency && unit) return context.error("NumberFormat options `currency` and `unit` are mutually exclusive");
		let minFractionDigits = null;
		if (options["min-fraction-digits"]) {
			minFractionDigits = context.parse(options["min-fraction-digits"], 1, NumberType);
			if (!minFractionDigits) return null;
		}
		let maxFractionDigits = null;
		if (options["max-fraction-digits"]) {
			maxFractionDigits = context.parse(options["max-fraction-digits"], 1, NumberType);
			if (!maxFractionDigits) return null;
		}
		return new NumberFormat(number, locale, currency, unit, minFractionDigits, maxFractionDigits);
	}
	evaluate(ctx) {
		return new Intl.NumberFormat(this.locale ? this.locale.evaluate(ctx) : [], {
			style: this.currency ? "currency" : this.unit ? "unit" : "decimal",
			currency: this.currency ? this.currency.evaluate(ctx) : void 0,
			unit: this.unit ? this.unit.evaluate(ctx) : void 0,
			minimumFractionDigits: this.minFractionDigits ? this.minFractionDigits.evaluate(ctx) : void 0,
			maximumFractionDigits: this.maxFractionDigits ? this.maxFractionDigits.evaluate(ctx) : void 0
		}).format(this.number.evaluate(ctx));
	}
	eachChild(fn) {
		fn(this.number);
		if (this.locale) fn(this.locale);
		if (this.currency) fn(this.currency);
		if (this.unit) fn(this.unit);
		if (this.minFractionDigits) fn(this.minFractionDigits);
		if (this.maxFractionDigits) fn(this.maxFractionDigits);
	}
	outputDefined() {
		return false;
	}
};
//#endregion
//#region src/expression/definitions/format.ts
var FormatExpression = class FormatExpression {
	constructor(sections) {
		this.type = FormattedType;
		this.sections = sections;
	}
	static parse(args, context) {
		if (args.length < 2) return context.error("Expected at least one argument.");
		const firstArg = args[1];
		if (!Array.isArray(firstArg) && typeof firstArg === "object") return context.error("First argument must be an image or text section.");
		const sections = [];
		let nextTokenMayBeObject = false;
		for (let i = 1; i <= args.length - 1; ++i) {
			const arg = args[i];
			if (nextTokenMayBeObject && typeof arg === "object" && !Array.isArray(arg)) {
				nextTokenMayBeObject = false;
				let scale = null;
				if (arg["font-scale"]) {
					scale = context.parse(arg["font-scale"], 1, NumberType);
					if (!scale) return null;
				}
				let font = null;
				if (arg["text-font"]) {
					font = context.parse(arg["text-font"], 1, array(StringType));
					if (!font) return null;
				}
				let textColor = null;
				if (arg["text-color"]) {
					textColor = context.parse(arg["text-color"], 1, ColorType);
					if (!textColor) return null;
				}
				let verticalAlign = null;
				if (arg["vertical-align"]) {
					if (typeof arg["vertical-align"] === "string" && !VERTICAL_ALIGN_OPTIONS.includes(arg["vertical-align"])) return context.error(`'vertical-align' must be one of: 'bottom', 'center', 'top' but found '${arg["vertical-align"]}' instead.`);
					verticalAlign = context.parse(arg["vertical-align"], 1, StringType);
					if (!verticalAlign) return null;
				}
				const lastExpression = sections[sections.length - 1];
				lastExpression.scale = scale;
				lastExpression.font = font;
				lastExpression.textColor = textColor;
				lastExpression.verticalAlign = verticalAlign;
			} else {
				const content = context.parse(args[i], 1, ValueType);
				if (!content) return null;
				const kind = content.type.kind;
				if (kind !== "string" && kind !== "value" && kind !== "null" && kind !== "resolvedImage") return context.error("Formatted text type must be 'string', 'value', 'image' or 'null'.");
				nextTokenMayBeObject = true;
				sections.push({
					content,
					scale: null,
					font: null,
					textColor: null,
					verticalAlign: null
				});
			}
		}
		return new FormatExpression(sections);
	}
	evaluate(ctx) {
		const evaluateSection = (section) => {
			const evaluatedContent = section.content.evaluate(ctx);
			if (typeOf(evaluatedContent) === ResolvedImageType) return new FormattedSection("", evaluatedContent, null, null, null, section.verticalAlign ? section.verticalAlign.evaluate(ctx) : null);
			return new FormattedSection(valueToString(evaluatedContent), null, section.scale ? section.scale.evaluate(ctx) : null, section.font ? section.font.evaluate(ctx).join(",") : null, section.textColor ? section.textColor.evaluate(ctx) : null, section.verticalAlign ? section.verticalAlign.evaluate(ctx) : null);
		};
		return new Formatted(this.sections.map(evaluateSection));
	}
	eachChild(fn) {
		for (const section of this.sections) {
			fn(section.content);
			if (section.scale) fn(section.scale);
			if (section.font) fn(section.font);
			if (section.textColor) fn(section.textColor);
			if (section.verticalAlign) fn(section.verticalAlign);
		}
	}
	outputDefined() {
		return false;
	}
};
//#endregion
//#region src/expression/definitions/image.ts
var ImageExpression = class ImageExpression {
	constructor(input) {
		this.type = ResolvedImageType;
		this.input = input;
	}
	static parse(args, context) {
		if (args.length !== 2) return context.error("Expected two arguments.");
		const name = context.parse(args[1], 1, StringType);
		if (!name) return context.error("No image name provided.");
		return new ImageExpression(name);
	}
	evaluate(ctx) {
		const evaluatedImageName = this.input.evaluate(ctx);
		const value = ResolvedImage.fromString(evaluatedImageName);
		if (value && ctx.availableImages) value.available = ctx.availableImages.indexOf(evaluatedImageName) > -1;
		return value;
	}
	eachChild(fn) {
		fn(this.input);
	}
	outputDefined() {
		return false;
	}
};
//#endregion
//#region src/expression/definitions/length.ts
var Length = class Length {
	constructor(input, key) {
		this.input = input;
		this.key = key;
		this.type = NumberType;
	}
	static parse(args, context) {
		if (args.length !== 2) return context.error(`Expected 1 argument, but found ${args.length - 1} instead.`);
		const input = context.parse(args[1], 1);
		if (!input) return null;
		if (input.type.kind !== "array" && input.type.kind !== "string" && input.type.kind !== "value") return context.error(`Expected argument of type string or array, but found ${typeToString(input.type)} instead.`);
		return new Length(input, context.key);
	}
	evaluate(ctx) {
		const input = this.input.evaluate(ctx);
		if (typeof input === "string") return [...input].length;
		else if (Array.isArray(input)) return input.length;
		else throw new RuntimeError(`Expected value to be of type string or array, but found ${typeToString(typeOf(input))} instead.`, this.key);
	}
	eachChild(fn) {
		fn(this.input);
	}
	outputDefined() {
		return false;
	}
};
//#endregion
//#region src/util/geometry_util.ts
const EXTENT = 8192;
function getTileCoordinates(p, canonical) {
	const x = mercatorXfromLng(p[0]);
	const y = mercatorYfromLat(p[1]);
	const tilesAtZoom = Math.pow(2, canonical.z);
	return [Math.round(x * tilesAtZoom * EXTENT), Math.round(y * tilesAtZoom * EXTENT)];
}
function getLngLatFromTileCoord(coord, canonical) {
	const tilesAtZoom = Math.pow(2, canonical.z);
	const x = (coord[0] / EXTENT + canonical.x) / tilesAtZoom;
	const y = (coord[1] / EXTENT + canonical.y) / tilesAtZoom;
	return [lngFromMercatorXfromLng(x), latFromMercatorY(y)];
}
function mercatorXfromLng(lng) {
	return (180 + lng) / 360;
}
function lngFromMercatorXfromLng(mercatorX) {
	return mercatorX * 360 - 180;
}
function mercatorYfromLat(lat) {
	return (180 - 180 / Math.PI * Math.log(Math.tan(Math.PI / 4 + lat * Math.PI / 360))) / 360;
}
function latFromMercatorY(mercatorY) {
	return 360 / Math.PI * Math.atan(Math.exp((180 - mercatorY * 360) * Math.PI / 180)) - 90;
}
function updateBBox(bbox, coord) {
	bbox[0] = Math.min(bbox[0], coord[0]);
	bbox[1] = Math.min(bbox[1], coord[1]);
	bbox[2] = Math.max(bbox[2], coord[0]);
	bbox[3] = Math.max(bbox[3], coord[1]);
}
function boxWithinBox(bbox1, bbox2) {
	if (bbox1[0] <= bbox2[0]) return false;
	if (bbox1[2] >= bbox2[2]) return false;
	if (bbox1[1] <= bbox2[1]) return false;
	if (bbox1[3] >= bbox2[3]) return false;
	return true;
}
function rayIntersect(p, p1, p2) {
	return p1[1] > p[1] !== p2[1] > p[1] && p[0] < (p2[0] - p1[0]) * (p[1] - p1[1]) / (p2[1] - p1[1]) + p1[0];
}
function pointOnBoundary(p, p1, p2) {
	const x1 = p[0] - p1[0];
	const y1 = p[1] - p1[1];
	const x2 = p[0] - p2[0];
	const y2 = p[1] - p2[1];
	return x1 * y2 - x2 * y1 === 0 && x1 * x2 <= 0 && y1 * y2 <= 0;
}
function segmentIntersectSegment(a, b, c, d) {
	const vectorP = [b[0] - a[0], b[1] - a[1]];
	if (perp([d[0] - c[0], d[1] - c[1]], vectorP) === 0) return false;
	if (twoSided(a, b, c, d) && twoSided(c, d, a, b)) return true;
	return false;
}
function lineIntersectPolygon(p1, p2, polygon) {
	for (const ring of polygon) for (let j = 0; j < ring.length - 1; ++j) if (segmentIntersectSegment(p1, p2, ring[j], ring[j + 1])) return true;
	return false;
}
function pointWithinPolygon(point, rings, trueIfOnBoundary = false) {
	let inside = false;
	for (const ring of rings) for (let j = 0; j < ring.length - 1; j++) {
		if (pointOnBoundary(point, ring[j], ring[j + 1])) return trueIfOnBoundary;
		if (rayIntersect(point, ring[j], ring[j + 1])) inside = !inside;
	}
	return inside;
}
function pointWithinPolygons(point, polygons) {
	for (const polygon of polygons) if (pointWithinPolygon(point, polygon)) return true;
	return false;
}
function lineStringWithinPolygon(line, polygon) {
	for (const point of line) if (!pointWithinPolygon(point, polygon)) return false;
	for (let i = 0; i < line.length - 1; ++i) if (lineIntersectPolygon(line[i], line[i + 1], polygon)) return false;
	return true;
}
function lineStringWithinPolygons(line, polygons) {
	for (const polygon of polygons) if (lineStringWithinPolygon(line, polygon)) return true;
	return false;
}
function perp(v1, v2) {
	return v1[0] * v2[1] - v1[1] * v2[0];
}
function twoSided(p1, p2, q1, q2) {
	const x1 = p1[0] - q1[0];
	const y1 = p1[1] - q1[1];
	const x2 = p2[0] - q1[0];
	const y2 = p2[1] - q1[1];
	const x3 = q2[0] - q1[0];
	const y3 = q2[1] - q1[1];
	const det1 = x1 * y3 - x3 * y1;
	const det2 = x2 * y3 - x3 * y2;
	if (det1 > 0 && det2 < 0 || det1 < 0 && det2 > 0) return true;
	return false;
}
//#endregion
//#region src/expression/definitions/within.ts
function getTilePolygon(coordinates, bbox, canonical) {
	const polygon = [];
	for (let i = 0; i < coordinates.length; i++) {
		const ring = [];
		for (let j = 0; j < coordinates[i].length; j++) {
			const coord = getTileCoordinates(coordinates[i][j], canonical);
			updateBBox(bbox, coord);
			ring.push(coord);
		}
		polygon.push(ring);
	}
	return polygon;
}
function getTilePolygons(coordinates, bbox, canonical) {
	const polygons = [];
	for (let i = 0; i < coordinates.length; i++) {
		const polygon = getTilePolygon(coordinates[i], bbox, canonical);
		polygons.push(polygon);
	}
	return polygons;
}
function updatePoint(p, bbox, polyBBox, worldSize) {
	if (p[0] < polyBBox[0] || p[0] > polyBBox[2]) {
		const halfWorldSize = worldSize * .5;
		let shift = p[0] - polyBBox[0] > halfWorldSize ? -worldSize : polyBBox[0] - p[0] > halfWorldSize ? worldSize : 0;
		if (shift === 0) shift = p[0] - polyBBox[2] > halfWorldSize ? -worldSize : polyBBox[2] - p[0] > halfWorldSize ? worldSize : 0;
		p[0] += shift;
	}
	updateBBox(bbox, p);
}
function resetBBox(bbox) {
	bbox[0] = bbox[1] = Infinity;
	bbox[2] = bbox[3] = -Infinity;
}
function getTilePoints(geometry, pointBBox, polyBBox, canonical) {
	const worldSize = Math.pow(2, canonical.z) * EXTENT;
	const shifts = [canonical.x * EXTENT, canonical.y * EXTENT];
	const tilePoints = [];
	for (const points of geometry) for (const point of points) {
		const p = [point.x + shifts[0], point.y + shifts[1]];
		updatePoint(p, pointBBox, polyBBox, worldSize);
		tilePoints.push(p);
	}
	return tilePoints;
}
function getTileLines(geometry, lineBBox, polyBBox, canonical) {
	const worldSize = Math.pow(2, canonical.z) * EXTENT;
	const shifts = [canonical.x * EXTENT, canonical.y * EXTENT];
	const tileLines = [];
	for (const line of geometry) {
		const tileLine = [];
		for (const point of line) {
			const p = [point.x + shifts[0], point.y + shifts[1]];
			updateBBox(lineBBox, p);
			tileLine.push(p);
		}
		tileLines.push(tileLine);
	}
	if (lineBBox[2] - lineBBox[0] <= worldSize / 2) {
		resetBBox(lineBBox);
		for (const line of tileLines) for (const p of line) updatePoint(p, lineBBox, polyBBox, worldSize);
	}
	return tileLines;
}
function pointsWithinPolygons(ctx, polygonGeometry) {
	const pointBBox = [
		Infinity,
		Infinity,
		-Infinity,
		-Infinity
	];
	const polyBBox = [
		Infinity,
		Infinity,
		-Infinity,
		-Infinity
	];
	const canonical = ctx.canonicalID();
	if (polygonGeometry.type === "Polygon") {
		const tilePolygon = getTilePolygon(polygonGeometry.coordinates, polyBBox, canonical);
		const tilePoints = getTilePoints(ctx.geometry(), pointBBox, polyBBox, canonical);
		if (!boxWithinBox(pointBBox, polyBBox)) return false;
		for (const point of tilePoints) if (!pointWithinPolygon(point, tilePolygon)) return false;
	}
	if (polygonGeometry.type === "MultiPolygon") {
		const tilePolygons = getTilePolygons(polygonGeometry.coordinates, polyBBox, canonical);
		const tilePoints = getTilePoints(ctx.geometry(), pointBBox, polyBBox, canonical);
		if (!boxWithinBox(pointBBox, polyBBox)) return false;
		for (const point of tilePoints) if (!pointWithinPolygons(point, tilePolygons)) return false;
	}
	return true;
}
function linesWithinPolygons(ctx, polygonGeometry) {
	const lineBBox = [
		Infinity,
		Infinity,
		-Infinity,
		-Infinity
	];
	const polyBBox = [
		Infinity,
		Infinity,
		-Infinity,
		-Infinity
	];
	const canonical = ctx.canonicalID();
	if (polygonGeometry.type === "Polygon") {
		const tilePolygon = getTilePolygon(polygonGeometry.coordinates, polyBBox, canonical);
		const tileLines = getTileLines(ctx.geometry(), lineBBox, polyBBox, canonical);
		if (!boxWithinBox(lineBBox, polyBBox)) return false;
		for (const line of tileLines) if (!lineStringWithinPolygon(line, tilePolygon)) return false;
	}
	if (polygonGeometry.type === "MultiPolygon") {
		const tilePolygons = getTilePolygons(polygonGeometry.coordinates, polyBBox, canonical);
		const tileLines = getTileLines(ctx.geometry(), lineBBox, polyBBox, canonical);
		if (!boxWithinBox(lineBBox, polyBBox)) return false;
		for (const line of tileLines) if (!lineStringWithinPolygons(line, tilePolygons)) return false;
	}
	return true;
}
var Within = class Within {
	constructor(geojson, geometries) {
		this.type = BooleanType;
		this.geojson = geojson;
		this.geometries = geometries;
	}
	static parse(args, context) {
		if (args.length !== 2) return context.error(`'within' expression requires exactly one argument, but found ${args.length - 1} instead.`);
		if (isValue(args[1])) {
			const geojson = args[1];
			if (geojson.type === "FeatureCollection") {
				const polygonsCoords = [];
				for (const polygon of geojson.features) {
					const { type, coordinates } = polygon.geometry;
					if (type === "Polygon") polygonsCoords.push(coordinates);
					if (type === "MultiPolygon") polygonsCoords.push(...coordinates);
				}
				if (polygonsCoords.length) return new Within(geojson, {
					type: "MultiPolygon",
					coordinates: polygonsCoords
				});
			} else if (geojson.type === "Feature") {
				const type = geojson.geometry.type;
				if (type === "Polygon" || type === "MultiPolygon") return new Within(geojson, geojson.geometry);
			} else if (geojson.type === "Polygon" || geojson.type === "MultiPolygon") return new Within(geojson, geojson);
		}
		return context.error("'within' expression requires valid geojson object that contains polygon geometry type.");
	}
	evaluate(ctx) {
		if (ctx.geometry() != null && ctx.canonicalID() != null) {
			if (ctx.geometryType() === "Point") return pointsWithinPolygons(ctx, this.geometries);
			else if (ctx.geometryType() === "LineString") return linesWithinPolygons(ctx, this.geometries);
		}
		return false;
	}
	eachChild() {}
	outputDefined() {
		return true;
	}
};
//#endregion
//#region node_modules/tinyqueue/index.js
var TinyQueue = class {
	constructor(data = [], compare = (a, b) => a < b ? -1 : a > b ? 1 : 0) {
		this.data = data;
		this.length = this.data.length;
		this.compare = compare;
		if (this.length > 0) for (let i = (this.length >> 1) - 1; i >= 0; i--) this._down(i);
	}
	push(item) {
		this.data.push(item);
		this._up(this.length++);
	}
	pop() {
		if (this.length === 0) return void 0;
		const top = this.data[0];
		const bottom = this.data.pop();
		if (--this.length > 0) {
			this.data[0] = bottom;
			this._down(0);
		}
		return top;
	}
	peek() {
		return this.data[0];
	}
	_up(pos) {
		const { data, compare } = this;
		const item = data[pos];
		while (pos > 0) {
			const parent = pos - 1 >> 1;
			const current = data[parent];
			if (compare(item, current) >= 0) break;
			data[pos] = current;
			pos = parent;
		}
		data[pos] = item;
	}
	_down(pos) {
		const { data, compare } = this;
		const halfLength = this.length >> 1;
		const item = data[pos];
		while (pos < halfLength) {
			let bestChild = (pos << 1) + 1;
			const right = bestChild + 1;
			if (right < this.length && compare(data[right], data[bestChild]) < 0) bestChild = right;
			if (compare(data[bestChild], item) >= 0) break;
			data[pos] = data[bestChild];
			pos = bestChild;
		}
		data[pos] = item;
	}
};
//#endregion
//#region node_modules/quickselect/index.js
/**
* Rearranges items so that all items in the [left, k] are the smallest.
* The k-th element will have the (k - left + 1)-th smallest value in [left, right].
*
* @template T
* @param {T[]} arr the array to partially sort (in place)
* @param {number} k middle index for partial sorting (as defined above)
* @param {number} [left=0] left index of the range to sort
* @param {number} [right=arr.length-1] right index
* @param {(a: T, b: T) => number} [compare = (a, b) => a - b] compare function
*/
function quickselect(arr, k, left = 0, right = arr.length - 1, compare = defaultCompare) {
	while (right > left) {
		if (right - left > 600) {
			const n = right - left + 1;
			const m = k - left + 1;
			const z = Math.log(n);
			const s = .5 * Math.exp(2 * z / 3);
			const sd = .5 * Math.sqrt(z * s * (n - s) / n) * (m - n / 2 < 0 ? -1 : 1);
			quickselect(arr, k, Math.max(left, Math.floor(k - m * s / n + sd)), Math.min(right, Math.floor(k + (n - m) * s / n + sd)), compare);
		}
		const t = arr[k];
		let i = left;
		/** @type {number} */
		let j = right;
		swap(arr, left, k);
		if (compare(arr[right], t) > 0) swap(arr, left, right);
		while (i < j) {
			swap(arr, i, j);
			i++;
			j--;
			while (compare(arr[i], t) < 0) i++;
			while (compare(arr[j], t) > 0) j--;
		}
		if (compare(arr[left], t) === 0) swap(arr, left, j);
		else {
			j++;
			swap(arr, j, right);
		}
		if (j <= k) left = j + 1;
		if (k <= j) right = j - 1;
	}
}
/**
* @template T
* @param {T[]} arr
* @param {number} i
* @param {number} j
*/
function swap(arr, i, j) {
	const tmp = arr[i];
	arr[i] = arr[j];
	arr[j] = tmp;
}
/**
* @template T
* @param {T} a
* @param {T} b
* @returns {number}
*/
function defaultCompare(a, b) {
	return a < b ? -1 : a > b ? 1 : 0;
}
//#endregion
//#region src/util/classify_rings.ts
/**
* Classifies an array of rings into polygons with outer rings and holes
* @param rings - the rings to classify
* @param maxRings - the maximum number of rings to include in a polygon, use 0 to include all rings
* @returns an array of polygons with internal rings as holes
*/
function classifyRings(rings, maxRings) {
	if (rings.length <= 1) return [rings];
	const polygons = [];
	let polygon;
	let ccw;
	for (const ring of rings) {
		const area = calculateSignedArea(ring);
		if (area === 0) continue;
		ring.area = Math.abs(area);
		if (ccw === void 0) ccw = area < 0;
		if (ccw === area < 0) {
			if (polygon) polygons.push(polygon);
			polygon = [ring];
		} else polygon.push(ring);
	}
	if (polygon) polygons.push(polygon);
	if (maxRings > 1) for (let j = 0; j < polygons.length; j++) {
		if (polygons[j].length <= maxRings) continue;
		quickselect(polygons[j], maxRings, 1, polygons[j].length - 1, compareAreas);
		polygons[j] = polygons[j].slice(0, maxRings);
	}
	return polygons;
}
function compareAreas(a, b) {
	return b.area - a.area;
}
/**
* Returns the signed area for the polygon ring.  Positive areas are exterior rings and
* have a clockwise winding.  Negative areas are interior rings and have a counter clockwise
* ordering.
*
* @param ring - Exterior or interior ring
* @returns Signed area
*/
function calculateSignedArea(ring) {
	let sum = 0;
	for (let i = 0, len = ring.length, j = len - 1, p1, p2; i < len; j = i++) {
		p1 = ring[i];
		p2 = ring[j];
		sum += (p2.x - p1.x) * (p1.y + p2.y);
	}
	return sum;
}
//#endregion
//#region src/util/cheap_ruler.ts
const RE = 6378.137;
const E2 = .0066943799901413165;
const RAD = Math.PI / 180;
var CheapRuler = class {
	constructor(lat) {
		const m = RAD * RE * 1e3;
		const coslat = Math.cos(lat * RAD);
		const w2 = 1 / (1 - E2 * (1 - coslat * coslat));
		const w = Math.sqrt(w2);
		this.kx = m * w * coslat;
		this.ky = m * w * w2 * .9933056200098587;
	}
	/**
	* Given two points of the form [longitude, latitude], returns the distance.
	*
	* @param a - point [longitude, latitude]
	* @param b - point [longitude, latitude]
	* @returns distance
	* @example
	* const distance = ruler.distance([30.5, 50.5], [30.51, 50.49]);
	* //=distance
	*/
	distance(a, b) {
		const dx = this.wrap(a[0] - b[0]) * this.kx;
		const dy = (a[1] - b[1]) * this.ky;
		return Math.sqrt(dx * dx + dy * dy);
	}
	/**
	* Returns an object of the form {point, index, t}, where point is closest point on the line
	* from the given point, index is the start index of the segment with the closest point,
	* and t is a parameter from 0 to 1 that indicates where the closest point is on that segment.
	*
	* @param line - an array of points that form the line
	* @param p - point [longitude, latitude]
	* @returns the nearest point, its index in the array and the proportion along the line
	* @example
	* const point = ruler.pointOnLine(line, [-67.04, 50.5]).point;
	* //=point
	*/
	pointOnLine(line, p) {
		let minDist = Infinity;
		let minX, minY, minI, minT;
		for (let i = 0; i < line.length - 1; i++) {
			let x = line[i][0];
			let y = line[i][1];
			let dx = this.wrap(line[i + 1][0] - x) * this.kx;
			let dy = (line[i + 1][1] - y) * this.ky;
			let t = 0;
			if (dx !== 0 || dy !== 0) {
				t = (this.wrap(p[0] - x) * this.kx * dx + (p[1] - y) * this.ky * dy) / (dx * dx + dy * dy);
				if (t > 1) {
					x = line[i + 1][0];
					y = line[i + 1][1];
				} else if (t > 0) {
					x += dx / this.kx * t;
					y += dy / this.ky * t;
				}
			}
			dx = this.wrap(p[0] - x) * this.kx;
			dy = (p[1] - y) * this.ky;
			const sqDist = dx * dx + dy * dy;
			if (sqDist < minDist) {
				minDist = sqDist;
				minX = x;
				minY = y;
				minI = i;
				minT = t;
			}
		}
		return {
			point: [minX, minY],
			index: minI,
			t: Math.max(0, Math.min(1, minT))
		};
	}
	wrap(deg) {
		while (deg < -180) deg += 360;
		while (deg > 180) deg -= 360;
		return deg;
	}
};
//#endregion
//#region src/expression/definitions/distance.ts
const MinPointsSize = 100;
const MinLinePointsSize = 50;
function compareDistPair(a, b) {
	return b[0] - a[0];
}
function getRangeSize(range) {
	return range[1] - range[0] + 1;
}
function isRangeSafe(range, threshold) {
	return range[1] >= range[0] && range[1] < threshold;
}
function splitRange(range, isLine) {
	if (range[0] > range[1]) return [null, null];
	const size = getRangeSize(range);
	if (isLine) {
		if (size === 2) return [range, null];
		const size1 = Math.floor(size / 2);
		return [[range[0], range[0] + size1], [range[0] + size1, range[1]]];
	}
	if (size === 1) return [range, null];
	const size1 = Math.floor(size / 2) - 1;
	return [[range[0], range[0] + size1], [range[0] + size1 + 1, range[1]]];
}
function getBBox(coords, range) {
	if (!isRangeSafe(range, coords.length)) return [
		Infinity,
		Infinity,
		-Infinity,
		-Infinity
	];
	const bbox = [
		Infinity,
		Infinity,
		-Infinity,
		-Infinity
	];
	for (let i = range[0]; i <= range[1]; ++i) updateBBox(bbox, coords[i]);
	return bbox;
}
function getPolygonBBox(polygon) {
	const bbox = [
		Infinity,
		Infinity,
		-Infinity,
		-Infinity
	];
	for (const ring of polygon) for (const coord of ring) updateBBox(bbox, coord);
	return bbox;
}
function isValidBBox(bbox) {
	return bbox[0] !== -Infinity && bbox[1] !== -Infinity && bbox[2] !== Infinity && bbox[3] !== Infinity;
}
function bboxToBBoxDistance(bbox1, bbox2, ruler) {
	if (!isValidBBox(bbox1) || !isValidBBox(bbox2)) return NaN;
	let dx = 0;
	let dy = 0;
	if (bbox1[2] < bbox2[0]) dx = bbox2[0] - bbox1[2];
	if (bbox1[0] > bbox2[2]) dx = bbox1[0] - bbox2[2];
	if (bbox1[1] > bbox2[3]) dy = bbox1[1] - bbox2[3];
	if (bbox1[3] < bbox2[1]) dy = bbox2[1] - bbox1[3];
	return ruler.distance([0, 0], [dx, dy]);
}
function pointToLineDistance(point, line, ruler) {
	const nearestPoint = ruler.pointOnLine(line, point);
	return ruler.distance(point, nearestPoint.point);
}
function segmentToSegmentDistance(p1, p2, q1, q2, ruler) {
	const dist1 = Math.min(pointToLineDistance(p1, [q1, q2], ruler), pointToLineDistance(p2, [q1, q2], ruler));
	const dist2 = Math.min(pointToLineDistance(q1, [p1, p2], ruler), pointToLineDistance(q2, [p1, p2], ruler));
	return Math.min(dist1, dist2);
}
function lineToLineDistance(line1, range1, line2, range2, ruler) {
	if (!(isRangeSafe(range1, line1.length) && isRangeSafe(range2, line2.length))) return Infinity;
	let dist = Infinity;
	for (let i = range1[0]; i < range1[1]; ++i) {
		const p1 = line1[i];
		const p2 = line1[i + 1];
		for (let j = range2[0]; j < range2[1]; ++j) {
			const q1 = line2[j];
			const q2 = line2[j + 1];
			if (segmentIntersectSegment(p1, p2, q1, q2)) return 0;
			dist = Math.min(dist, segmentToSegmentDistance(p1, p2, q1, q2, ruler));
		}
	}
	return dist;
}
function pointsToPointsDistance(points1, range1, points2, range2, ruler) {
	if (!(isRangeSafe(range1, points1.length) && isRangeSafe(range2, points2.length))) return NaN;
	let dist = Infinity;
	for (let i = range1[0]; i <= range1[1]; ++i) for (let j = range2[0]; j <= range2[1]; ++j) {
		dist = Math.min(dist, ruler.distance(points1[i], points2[j]));
		if (dist === 0) return dist;
	}
	return dist;
}
function pointToPolygonDistance(point, polygon, ruler) {
	if (pointWithinPolygon(point, polygon, true)) return 0;
	let dist = Infinity;
	for (const ring of polygon) {
		const front = ring[0];
		const back = ring[ring.length - 1];
		if (front !== back) {
			dist = Math.min(dist, pointToLineDistance(point, [back, front], ruler));
			if (dist === 0) return dist;
		}
		const nearestPoint = ruler.pointOnLine(ring, point);
		dist = Math.min(dist, ruler.distance(point, nearestPoint.point));
		if (dist === 0) return dist;
	}
	return dist;
}
function lineToPolygonDistance(line, range, polygon, ruler) {
	if (!isRangeSafe(range, line.length)) return NaN;
	for (let i = range[0]; i <= range[1]; ++i) if (pointWithinPolygon(line[i], polygon, true)) return 0;
	let dist = Infinity;
	for (let i = range[0]; i < range[1]; ++i) {
		const p1 = line[i];
		const p2 = line[i + 1];
		for (const ring of polygon) for (let j = 0, len = ring.length, k = len - 1; j < len; k = j++) {
			const q1 = ring[k];
			const q2 = ring[j];
			if (segmentIntersectSegment(p1, p2, q1, q2)) return 0;
			dist = Math.min(dist, segmentToSegmentDistance(p1, p2, q1, q2, ruler));
		}
	}
	return dist;
}
function polygonIntersect(poly1, poly2) {
	for (const ring of poly1) for (const point of ring) if (pointWithinPolygon(point, poly2, true)) return true;
	return false;
}
function polygonToPolygonDistance(polygon1, polygon2, ruler, currentMiniDist = Infinity) {
	const bbox1 = getPolygonBBox(polygon1);
	const bbox2 = getPolygonBBox(polygon2);
	if (currentMiniDist !== Infinity && bboxToBBoxDistance(bbox1, bbox2, ruler) >= currentMiniDist) return currentMiniDist;
	if (boxWithinBox(bbox1, bbox2)) {
		if (polygonIntersect(polygon1, polygon2)) return 0;
	} else if (polygonIntersect(polygon2, polygon1)) return 0;
	let dist = Infinity;
	for (const ring1 of polygon1) for (let i = 0, len1 = ring1.length, l = len1 - 1; i < len1; l = i++) {
		const p1 = ring1[l];
		const p2 = ring1[i];
		for (const ring2 of polygon2) for (let j = 0, len2 = ring2.length, k = len2 - 1; j < len2; k = j++) {
			const q1 = ring2[k];
			const q2 = ring2[j];
			if (segmentIntersectSegment(p1, p2, q1, q2)) return 0;
			dist = Math.min(dist, segmentToSegmentDistance(p1, p2, q1, q2, ruler));
		}
	}
	return dist;
}
function updateQueue(distQueue, miniDist, ruler, points, polyBBox, rangeA) {
	if (!rangeA) return;
	const tempDist = bboxToBBoxDistance(getBBox(points, rangeA), polyBBox, ruler);
	if (tempDist < miniDist) distQueue.push([
		tempDist,
		rangeA,
		[0, 0]
	]);
}
function updateQueueTwoSets(distQueue, miniDist, ruler, pointSet1, pointSet2, range1, range2) {
	if (!range1 || !range2) return;
	const tempDist = bboxToBBoxDistance(getBBox(pointSet1, range1), getBBox(pointSet2, range2), ruler);
	if (tempDist < miniDist) distQueue.push([
		tempDist,
		range1,
		range2
	]);
}
function pointsToPolygonDistance(points, isLine, polygon, ruler, currentMiniDist = Infinity) {
	let miniDist = Math.min(ruler.distance(points[0], polygon[0][0]), currentMiniDist);
	if (miniDist === 0) return miniDist;
	const distQueue = new TinyQueue([[
		0,
		[0, points.length - 1],
		[0, 0]
	]], compareDistPair);
	const polyBBox = getPolygonBBox(polygon);
	while (distQueue.length > 0) {
		const distPair = distQueue.pop();
		if (distPair[0] >= miniDist) continue;
		const range = distPair[1];
		const threshold = isLine ? MinLinePointsSize : MinPointsSize;
		if (getRangeSize(range) <= threshold) {
			if (!isRangeSafe(range, points.length)) return NaN;
			if (isLine) {
				const tempDist = lineToPolygonDistance(points, range, polygon, ruler);
				if (isNaN(tempDist) || tempDist === 0) return tempDist;
				miniDist = Math.min(miniDist, tempDist);
			} else for (let i = range[0]; i <= range[1]; ++i) {
				const tempDist = pointToPolygonDistance(points[i], polygon, ruler);
				miniDist = Math.min(miniDist, tempDist);
				if (miniDist === 0) return 0;
			}
		} else {
			const newRangesA = splitRange(range, isLine);
			updateQueue(distQueue, miniDist, ruler, points, polyBBox, newRangesA[0]);
			updateQueue(distQueue, miniDist, ruler, points, polyBBox, newRangesA[1]);
		}
	}
	return miniDist;
}
function pointSetToPointSetDistance(pointSet1, isLine1, pointSet2, isLine2, ruler, currentMiniDist = Infinity) {
	let miniDist = Math.min(currentMiniDist, ruler.distance(pointSet1[0], pointSet2[0]));
	if (miniDist === 0) return miniDist;
	const distQueue = new TinyQueue([[
		0,
		[0, pointSet1.length - 1],
		[0, pointSet2.length - 1]
	]], compareDistPair);
	while (distQueue.length > 0) {
		const distPair = distQueue.pop();
		if (distPair[0] >= miniDist) continue;
		const rangeA = distPair[1];
		const rangeB = distPair[2];
		const threshold1 = isLine1 ? MinLinePointsSize : MinPointsSize;
		const threshold2 = isLine2 ? MinLinePointsSize : MinPointsSize;
		if (getRangeSize(rangeA) <= threshold1 && getRangeSize(rangeB) <= threshold2) {
			if (!isRangeSafe(rangeA, pointSet1.length) && isRangeSafe(rangeB, pointSet2.length)) return NaN;
			let tempDist;
			if (isLine1 && isLine2) {
				tempDist = lineToLineDistance(pointSet1, rangeA, pointSet2, rangeB, ruler);
				miniDist = Math.min(miniDist, tempDist);
			} else if (isLine1 && !isLine2) {
				const sublibe = pointSet1.slice(rangeA[0], rangeA[1] + 1);
				for (let i = rangeB[0]; i <= rangeB[1]; ++i) {
					tempDist = pointToLineDistance(pointSet2[i], sublibe, ruler);
					miniDist = Math.min(miniDist, tempDist);
					if (miniDist === 0) return miniDist;
				}
			} else if (!isLine1 && isLine2) {
				const sublibe = pointSet2.slice(rangeB[0], rangeB[1] + 1);
				for (let i = rangeA[0]; i <= rangeA[1]; ++i) {
					tempDist = pointToLineDistance(pointSet1[i], sublibe, ruler);
					miniDist = Math.min(miniDist, tempDist);
					if (miniDist === 0) return miniDist;
				}
			} else {
				tempDist = pointsToPointsDistance(pointSet1, rangeA, pointSet2, rangeB, ruler);
				miniDist = Math.min(miniDist, tempDist);
			}
		} else {
			const newRangesA = splitRange(rangeA, isLine1);
			const newRangesB = splitRange(rangeB, isLine2);
			updateQueueTwoSets(distQueue, miniDist, ruler, pointSet1, pointSet2, newRangesA[0], newRangesB[0]);
			updateQueueTwoSets(distQueue, miniDist, ruler, pointSet1, pointSet2, newRangesA[0], newRangesB[1]);
			updateQueueTwoSets(distQueue, miniDist, ruler, pointSet1, pointSet2, newRangesA[1], newRangesB[0]);
			updateQueueTwoSets(distQueue, miniDist, ruler, pointSet1, pointSet2, newRangesA[1], newRangesB[1]);
		}
	}
	return miniDist;
}
function pointToGeometryDistance(ctx, geometries) {
	const tilePoints = ctx.geometry();
	const pointPosition = tilePoints.flat().map((p) => getLngLatFromTileCoord([p.x, p.y], ctx.canonical));
	if (tilePoints.length === 0) return NaN;
	const ruler = new CheapRuler(pointPosition[0][1]);
	let dist = Infinity;
	for (const geometry of geometries) {
		switch (geometry.type) {
			case "Point":
				dist = Math.min(dist, pointSetToPointSetDistance(pointPosition, false, [geometry.coordinates], false, ruler, dist));
				break;
			case "LineString":
				dist = Math.min(dist, pointSetToPointSetDistance(pointPosition, false, geometry.coordinates, true, ruler, dist));
				break;
			case "Polygon": dist = Math.min(dist, pointsToPolygonDistance(pointPosition, false, geometry.coordinates, ruler, dist));
		}
		if (dist === 0) return dist;
	}
	return dist;
}
function lineStringToGeometryDistance(ctx, geometries) {
	const tileLine = ctx.geometry();
	const linePositions = tileLine.flat().map((p) => getLngLatFromTileCoord([p.x, p.y], ctx.canonical));
	if (tileLine.length === 0) return NaN;
	const ruler = new CheapRuler(linePositions[0][1]);
	let dist = Infinity;
	for (const geometry of geometries) {
		switch (geometry.type) {
			case "Point":
				dist = Math.min(dist, pointSetToPointSetDistance(linePositions, true, [geometry.coordinates], false, ruler, dist));
				break;
			case "LineString":
				dist = Math.min(dist, pointSetToPointSetDistance(linePositions, true, geometry.coordinates, true, ruler, dist));
				break;
			case "Polygon": dist = Math.min(dist, pointsToPolygonDistance(linePositions, true, geometry.coordinates, ruler, dist));
		}
		if (dist === 0) return dist;
	}
	return dist;
}
function polygonToGeometryDistance(ctx, geometries) {
	const tilePolygon = ctx.geometry();
	if (tilePolygon.length === 0 || tilePolygon[0].length === 0) return NaN;
	const polygons = classifyRings(tilePolygon, 0).map((polygon) => {
		return polygon.map((ring) => {
			return ring.map((p) => getLngLatFromTileCoord([p.x, p.y], ctx.canonical));
		});
	});
	const ruler = new CheapRuler(polygons[0][0][0][1]);
	let dist = Infinity;
	for (const geometry of geometries) for (const polygon of polygons) {
		switch (geometry.type) {
			case "Point":
				dist = Math.min(dist, pointsToPolygonDistance([geometry.coordinates], false, polygon, ruler, dist));
				break;
			case "LineString":
				dist = Math.min(dist, pointsToPolygonDistance(geometry.coordinates, true, polygon, ruler, dist));
				break;
			case "Polygon": dist = Math.min(dist, polygonToPolygonDistance(polygon, geometry.coordinates, ruler, dist));
		}
		if (dist === 0) return dist;
	}
	return dist;
}
function toSimpleGeometry(geometry) {
	if (geometry.type === "MultiPolygon") return geometry.coordinates.map((polygon) => {
		return {
			type: "Polygon",
			coordinates: polygon
		};
	});
	if (geometry.type === "MultiLineString") return geometry.coordinates.map((lineString) => {
		return {
			type: "LineString",
			coordinates: lineString
		};
	});
	if (geometry.type === "MultiPoint") return geometry.coordinates.map((point) => {
		return {
			type: "Point",
			coordinates: point
		};
	});
	return [geometry];
}
//#endregion
//#region src/expression/definitions/index.ts
const expressions$1 = {
	"==": Equals,
	"!=": NotEquals,
	">": GreaterThan,
	"<": LessThan,
	">=": GreaterThanOrEqual,
	"<=": LessThanOrEqual,
	array: Assertion,
	at: At,
	boolean: Assertion,
	case: Case,
	coalesce: Coalesce,
	collator: CollatorExpression,
	format: FormatExpression,
	image: ImageExpression,
	in: In,
	"index-of": IndexOf,
	interpolate: Interpolate,
	"interpolate-hcl": Interpolate,
	"interpolate-lab": Interpolate,
	length: Length,
	let: Let,
	literal: Literal,
	match: Match,
	number: Assertion,
	"number-format": NumberFormat,
	object: Assertion,
	semiliteral: class Semiliteral {
		constructor(arr) {
			let elementType = null;
			for (const expr of arr) if (!elementType) elementType = expr.type;
			else if (elementType === expr.type) continue;
			else {
				elementType = ValueType;
				break;
			}
			this.type = array(elementType ?? ValueType, arr.length);
			this.arr = arr;
		}
		static parse(args, context) {
			if (args.length !== 2) return context.error(`'semiliteral' expression requires exactly one argument, but found ${args.length - 1} instead.`);
			if (!isValue(args[1])) return context.error(`invalid value of type "${typeof args[1]}"`);
			const value = args[1];
			const type = typeOf(value);
			if (type.kind === "array") {
				const arr = value;
				const arrayContext = context.concat(1);
				const parsed = [];
				for (let i = 0; i < arr.length; i++) {
					const item = arrayContext.parse(arr[i], i, ValueType);
					if (!item) return null;
					parsed.push(item);
				}
				return new Semiliteral(parsed);
			} else return new Literal(type, value);
		}
		evaluate(ctx) {
			return this.arr.map((arg) => arg.evaluate(ctx));
		}
		eachChild(fn) {
			this.arr.forEach(fn);
		}
		outputDefined() {
			return this.arr.every((arg) => arg.outputDefined());
		}
	},
	slice: Slice,
	step: Step,
	string: Assertion,
	"to-boolean": Coercion,
	"to-color": Coercion,
	"to-number": Coercion,
	"to-string": Coercion,
	var: Var,
	within: Within,
	distance: class Distance {
		constructor(geojson, geometries) {
			this.type = NumberType;
			this.geojson = geojson;
			this.geometries = geometries;
		}
		static parse(args, context) {
			if (args.length !== 2) return context.error(`'distance' expression requires exactly one argument, but found ${args.length - 1} instead.`);
			if (isValue(args[1])) {
				const geojson = args[1];
				if (geojson.type === "FeatureCollection") return new Distance(geojson, geojson.features.map((feature) => toSimpleGeometry(feature.geometry)).flat());
				else if (geojson.type === "Feature") return new Distance(geojson, toSimpleGeometry(geojson.geometry));
				else if ("type" in geojson && "coordinates" in geojson) return new Distance(geojson, toSimpleGeometry(geojson));
			}
			return context.error("'distance' expression requires valid geojson object that contains polygon geometry type.");
		}
		evaluate(ctx) {
			if (ctx.geometry() != null && ctx.canonicalID() != null) {
				if (ctx.geometryType() === "Point") return pointToGeometryDistance(ctx, this.geometries);
				else if (ctx.geometryType() === "LineString") return lineStringToGeometryDistance(ctx, this.geometries);
				else if (ctx.geometryType() === "Polygon") return polygonToGeometryDistance(ctx, this.geometries);
			}
			return NaN;
		}
		eachChild() {}
		outputDefined() {
			return true;
		}
	},
	"global-state": class GlobalState {
		constructor(key) {
			this.key = key;
			this.type = ValueType;
		}
		static parse(args, context) {
			if (args.length !== 2) return context.error(`Expected 1 argument, but found ${args.length - 1} instead.`);
			const key = args[1];
			if (key === void 0 || key === null) return context.error("Global state property must be defined.");
			if (typeof key !== "string") return context.error(`Global state property must be string, but found ${typeof args[1]} instead.`);
			return new GlobalState(key);
		}
		evaluate(ctx) {
			const globalState = ctx.globals?.globalState;
			if (!globalState || Object.keys(globalState).length === 0) return null;
			return getOwn(globalState, this.key) ?? null;
		}
		eachChild() {}
		outputDefined() {
			return false;
		}
	}
};
//#endregion
//#region src/expression/index.ts
function isExpression(expression) {
	return Array.isArray(expression) && expression.length > 0 && typeof expression[0] === "string" && expression[0] in expressions$1;
}
//#endregion
//#region src/function/convert.ts
function convertLiteral(value) {
	return typeof value === "object" ? ["literal", value] : value;
}
function convertFunction(parameters, propertySpec) {
	let stops = parameters.stops;
	if (!stops) return convertIdentityFunction(parameters, propertySpec);
	const zoomAndFeatureDependent = stops && typeof stops[0][0] === "object";
	const featureDependent = zoomAndFeatureDependent || parameters.property !== void 0;
	const zoomDependent = zoomAndFeatureDependent || !featureDependent;
	stops = stops.map((stop) => {
		if (!featureDependent && propertySpec.tokens && typeof stop[1] === "string") return [stop[0], convertTokenString(stop[1])];
		return [stop[0], convertLiteral(stop[1])];
	});
	if (zoomAndFeatureDependent) return convertZoomAndPropertyFunction(parameters, propertySpec, stops);
	else if (zoomDependent) return convertZoomFunction(parameters, propertySpec, stops);
	else return convertPropertyFunction(parameters, propertySpec, stops);
}
function convertIdentityFunction(parameters, propertySpec) {
	const get = ["get", parameters.property];
	if (parameters.default === void 0) return propertySpec.type === "string" ? ["string", get] : get;
	else if (propertySpec.type === "enum") return [
		"match",
		get,
		Object.keys(propertySpec.values),
		get,
		parameters.default
	];
	else {
		const expression = [
			propertySpec.type === "color" ? "to-color" : propertySpec.type,
			get,
			convertLiteral(parameters.default)
		];
		if (propertySpec.type === "array") expression.splice(1, 0, propertySpec.value, propertySpec.length || null);
		return expression;
	}
}
function getInterpolateOperator(parameters) {
	switch (parameters.colorSpace) {
		case "hcl": return "interpolate-hcl";
		case "lab": return "interpolate-lab";
		default: return "interpolate";
	}
}
function convertZoomAndPropertyFunction(parameters, propertySpec, stops) {
	const featureFunctionParameters = {};
	const featureFunctionStops = {};
	const zoomStops = [];
	for (let s = 0; s < stops.length; s++) {
		const stop = stops[s];
		const zoom = stop[0].zoom;
		if (featureFunctionParameters[zoom] === void 0) {
			featureFunctionParameters[zoom] = {
				zoom,
				type: parameters.type,
				property: parameters.property,
				default: parameters.default
			};
			featureFunctionStops[zoom] = [];
			zoomStops.push(zoom);
		}
		featureFunctionStops[zoom].push([stop[0].value, stop[1]]);
	}
	if (getFunctionType({}, propertySpec) === "exponential") {
		const expression = [
			getInterpolateOperator(parameters),
			["linear"],
			["zoom"]
		];
		for (const z of zoomStops) appendStopPair(expression, z, convertPropertyFunction(featureFunctionParameters[z], propertySpec, featureFunctionStops[z]), false);
		return expression;
	} else {
		const expression = ["step", ["zoom"]];
		for (const z of zoomStops) appendStopPair(expression, z, convertPropertyFunction(featureFunctionParameters[z], propertySpec, featureFunctionStops[z]), true);
		fixupDegenerateStepCurve(expression);
		return expression;
	}
}
function coalesce(a, b) {
	if (a !== void 0) return a;
	if (b !== void 0) return b;
}
function getFallback(parameters, propertySpec) {
	const defaultValue = convertLiteral(coalesce(parameters.default, propertySpec.default));
	if (defaultValue === void 0 && propertySpec.type === "resolvedImage") return "";
	return defaultValue;
}
function convertPropertyFunction(parameters, propertySpec, stops) {
	const type = getFunctionType(parameters, propertySpec);
	const get = ["get", parameters.property];
	if (type === "categorical" && typeof stops[0][0] === "boolean") {
		const expression = ["case"];
		for (const stop of stops) expression.push([
			"==",
			get,
			stop[0]
		], stop[1]);
		expression.push(getFallback(parameters, propertySpec));
		return expression;
	} else if (type === "categorical") {
		const expression = ["match", get];
		for (const stop of stops) appendStopPair(expression, stop[0], stop[1], false);
		expression.push(getFallback(parameters, propertySpec));
		return expression;
	} else if (type === "interval") {
		const expression = ["step", ["number", get]];
		for (const stop of stops) appendStopPair(expression, stop[0], stop[1], true);
		fixupDegenerateStepCurve(expression);
		return parameters.default === void 0 ? expression : [
			"case",
			[
				"==",
				["typeof", get],
				"number"
			],
			expression,
			convertLiteral(parameters.default)
		];
	} else if (type === "exponential") {
		const base = parameters.base !== void 0 ? parameters.base : 1;
		const expression = [
			getInterpolateOperator(parameters),
			base === 1 ? ["linear"] : ["exponential", base],
			["number", get]
		];
		for (const stop of stops) appendStopPair(expression, stop[0], stop[1], false);
		return parameters.default === void 0 ? expression : [
			"case",
			[
				"==",
				["typeof", get],
				"number"
			],
			expression,
			convertLiteral(parameters.default)
		];
	} else throw new Error(`Unknown property function type ${type}`);
}
function convertZoomFunction(parameters, propertySpec, stops, input = ["zoom"]) {
	const type = getFunctionType(parameters, propertySpec);
	let expression;
	let isStep = false;
	if (type === "interval") {
		expression = ["step", input];
		isStep = true;
	} else if (type === "exponential") {
		const base = parameters.base !== void 0 ? parameters.base : 1;
		expression = [
			getInterpolateOperator(parameters),
			base === 1 ? ["linear"] : ["exponential", base],
			input
		];
	} else throw new Error(`Unknown zoom function type "${type}"`);
	for (const stop of stops) appendStopPair(expression, stop[0], stop[1], isStep);
	fixupDegenerateStepCurve(expression);
	return expression;
}
function fixupDegenerateStepCurve(expression) {
	if (expression[0] === "step" && expression.length === 3) {
		expression.push(0);
		expression.push(expression[3]);
	}
}
function appendStopPair(curve, input, output, isStep) {
	if (curve.length > 3 && input === curve[curve.length - 2]) return;
	if (!(isStep && curve.length === 2)) curve.push(input);
	curve.push(output);
}
function getFunctionType(parameters, propertySpec) {
	if (parameters.type) return parameters.type;
	else return propertySpec.expression.interpolated ? "exponential" : "interval";
}
function convertTokenString(s) {
	const result = ["concat"];
	const re = /{([^{}]+)}/g;
	let pos = 0;
	for (let match = re.exec(s); match !== null; match = re.exec(s)) {
		const literal = s.slice(pos, re.lastIndex - match[0].length);
		pos = re.lastIndex;
		if (literal.length > 0) result.push(literal);
		result.push(["get", match[1]]);
	}
	if (result.length === 1) return s;
	if (pos < s.length) result.push(s.slice(pos));
	else if (result.length === 2) return ["to-string", result[1]];
	return result;
}
//#endregion
//#region src/feature_filter/index.ts
function classifyChildren(children) {
	let sawLegacy = false;
	for (const child of children) {
		const classification = classifyFilter(child);
		if (classification === "expression") return "expression";
		if (classification === "legacy") sawLegacy = true;
	}
	return sawLegacy ? "legacy" : "neutral";
}
function classifyFilter(filter) {
	if (typeof filter === "boolean") return "neutral";
	if (!Array.isArray(filter) || filter.length === 0) return "legacy";
	switch (filter[0]) {
		case "has":
			if (filter.length < 2 || filter[1] === "$id" || filter[1] === "$type") return "legacy";
			return filter.length === 2 ? "neutral" : "expression";
		case "in": return filter.length >= 3 && (typeof filter[1] !== "string" || Array.isArray(filter[2])) ? "expression" : "legacy";
		case "!in":
		case "!has": return "legacy";
		case "==":
		case "!=":
		case ">":
		case ">=":
		case "<":
		case "<=": return filter.length !== 3 || Array.isArray(filter[1]) || Array.isArray(filter[2]) ? "expression" : "legacy";
		case "none": return "legacy";
		case "any":
		case "all": return classifyChildren(filter.slice(1));
		default: return "expression";
	}
}
function isExpressionFilter(filter) {
	return classifyFilter(filter) !== "legacy";
}
//#endregion
//#region src/feature_filter/convert.ts
function convertFilter(filter, expectedTypes = {}) {
	if (isExpressionFilter(filter)) return filter;
	if (!filter) return true;
	const legacyFilter = filter;
	const legacyOp = legacyFilter[0];
	if (filter.length <= 1) return legacyOp !== "any";
	switch (legacyOp) {
		case "==":
		case "!=":
		case "<":
		case ">":
		case "<=":
		case ">=": {
			const [, property, value] = filter;
			return convertComparisonOp(property, value, legacyOp, expectedTypes);
		}
		case "any": {
			const [, ...conditions] = legacyFilter;
			return ["any", ...conditions.map((f) => {
				const types = {};
				const child = convertFilter(f, types);
				const typechecks = runtimeTypeChecks(types);
				return typechecks === true ? child : [
					"case",
					typechecks,
					child,
					false
				];
			})];
		}
		case "all": {
			const [, ...conditions] = legacyFilter;
			const children = conditions.map((f) => convertFilter(f, expectedTypes));
			return children.length > 1 ? ["all", ...children] : children[0];
		}
		case "none": {
			const [, ...conditions] = legacyFilter;
			return ["!", convertFilter(["any", ...conditions], {})];
		}
		case "in": {
			const [, property, ...values] = legacyFilter;
			return convertInOp(property, values);
		}
		case "!in": {
			const [, property, ...values] = legacyFilter;
			return convertInOp(property, values, true);
		}
		case "has": return convertHasOp(legacyFilter[1]);
		case "!has": return ["!", convertHasOp(legacyFilter[1])];
		default: return true;
	}
}
function runtimeTypeChecks(expectedTypes) {
	const conditions = [];
	for (const property in expectedTypes) {
		const get = property === "$id" ? ["id"] : ["get", property];
		conditions.push([
			"==",
			["typeof", get],
			expectedTypes[property]
		]);
	}
	if (conditions.length === 0) return true;
	if (conditions.length === 1) return conditions[0];
	return ["all", ...conditions];
}
function convertComparisonOp(property, value, op, expectedTypes) {
	let get;
	if (property === "$type") return [
		op,
		["geometry-type"],
		value
	];
	else if (property === "$id") get = ["id"];
	else get = ["get", property];
	if (expectedTypes && value !== null) expectedTypes[property] = typeof value;
	if (op === "==" && property !== "$id" && value === null) return [
		"all",
		["has", property],
		[
			"==",
			get,
			null
		]
	];
	else if (op === "!=" && property !== "$id" && value === null) return [
		"any",
		["!", ["has", property]],
		[
			"!=",
			get,
			null
		]
	];
	return [
		op,
		get,
		value
	];
}
function convertInOp(property, values, negate = false) {
	if (values.length === 0) return negate;
	let get;
	if (property === "$type") get = ["geometry-type"];
	else if (property === "$id") get = ["id"];
	else get = ["get", property];
	let uniformTypes = true;
	const type = typeof values[0];
	for (const value of values) if (typeof value !== type) {
		uniformTypes = false;
		break;
	}
	if (uniformTypes && (type === "string" || type === "number")) {
		const uniqueValues = values.sort().filter((v, i) => i === 0 || values[i - 1] !== v);
		return [
			"match",
			get,
			uniqueValues,
			!negate,
			negate
		];
	}
	if (negate) return ["all", ...values.map((v) => [
		"!=",
		get,
		v
	])];
	else return ["any", ...values.map((v) => [
		"==",
		get,
		v
	])];
}
function convertHasOp(property) {
	if (property === "$type") return true;
	else if (property === "$id") return [
		"!=",
		["id"],
		null
	];
	else return ["has", property];
}
//#endregion
//#region src/migrate/expressions.ts
/**
* Migrate the given style object in place to use expressions. Specifically,
* this will convert (a) "stop" functions, and (b) legacy filters to their
* expression equivalents.
* @param style The style object to migrate.
* @returns The migrated style object.
*/
function expressions(style) {
	const converted = [];
	eachLayer(style, (layer) => {
		if (layer.filter) layer.filter = convertFilter(layer.filter);
	});
	eachProperty(style, {
		paint: true,
		layout: true
	}, ({ path, key, value, reference, set }) => {
		if (isExpression(value) || key.endsWith("-transition") || reference === null) return;
		if (typeof value === "object" && !Array.isArray(value)) {
			set(convertFunction(value, reference));
			converted.push(path.join("."));
		} else if (reference.tokens && typeof value === "string") set(convertTokenString(value));
	});
	return style;
}
//#endregion
//#region src/migrate/migrate_colors.ts
/**
* Migrate color style values to supported format.
*
* @param colorToMigrate Color value to migrate, could be a string or an expression.
* @returns Color style value in supported format.
*/
function migrateColors(colorToMigrate) {
	return JSON.parse(migrateHslColors(JSON.stringify(colorToMigrate)));
}
/**
* Created to migrate from colors supported by the former CSS color parsing
* library `csscolorparser` but not compliant with the CSS Color specification,
* like `hsl(900, 0.15, 90%)`.
*
* @param colorToMigrate Serialized color style value.
* @returns A serialized color style value in which all non-standard hsl color values
* have been converted to a format that complies with the CSS Color specification.
*
* @example
* migrateHslColors('"hsl(900, 0.15, 90%)"'); // returns '"hsl(900, 15%, 90%)"'
* migrateHslColors('"hsla(900, .15, .9)"'); // returns '"hsl(900, 15%, 90%)"'
* migrateHslColors('"hsl(900, 15%, 90%)"'); // returns '"hsl(900, 15%, 90%)"' - no changes
*/
function migrateHslColors(colorToMigrate) {
	return colorToMigrate.replace(/"hsla?\((.+?)\)"/gi, (match, hslArgs) => {
		const argsMatch = hslArgs.match(/^(.+?)\s*,\s*(.+?)\s*,\s*(.+?)(?:\s*,\s*(.+))?$/i);
		if (argsMatch) {
			let [h, s, l, a] = argsMatch.slice(1);
			[s, l] = [s, l].map((v) => v.endsWith("%") ? v : `${parseFloat(v) * 100}%`);
			return `"hsl${typeof a === "string" ? "a" : ""}(${[
				h,
				s,
				l,
				a
			].filter(Boolean).join(",")})"`;
		}
		return match;
	});
}
//#endregion
//#region src/migrate.ts
/**
* Migrate a Mapbox/MapLibre GL Style to the latest version.
*
* @param style - a MapLibre Style
* @returns a migrated style
* @example
* const fs = require('fs');
* const migrate = require('@maplibre/maplibre-gl-style-spec').migrate;
* const style = fs.readFileSync('./style.json', 'utf8');
* fs.writeFileSync('./style.json', JSON.stringify(migrate(style)));
*/
function migrate(style) {
	let migrated = false;
	if (style.version === 7) {
		style = migrateV8(style);
		migrated = true;
	}
	if (style.version === 8) {
		migrated = !!expressions(style);
		migrated = true;
	}
	eachProperty(style, {
		paint: true,
		layout: true
	}, ({ value, reference, set }) => {
		if (reference?.type === "color") set(migrateColors(value));
	});
	if (!migrated) throw new Error(`Cannot migrate from ${style.version}`);
	return style;
}
//#endregion
//#region bin/gl-style-migrate.ts
const argv = (0, import_minimist.default)(process.argv.slice(2));
if (argv.help || argv.h || !argv._.length && process.stdin.isTTY) help();
else console.log(format(migrate(JSON.parse(fs.default.readFileSync(argv._[0]).toString()))));
function help() {
	console.log("usage:");
	console.log("  gl-style-migrate style-v7.json > style-v8.json");
}
//#endregion

//# sourceMappingURL=gl-style-migrate.cjs.map