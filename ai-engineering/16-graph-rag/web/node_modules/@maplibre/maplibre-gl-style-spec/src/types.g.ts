// Generated code; do not edit. Edit build/generate-style-spec.ts instead.

export type ColorSpecification = string;

export type ProjectionDefinitionT = [string, string, number];
export type ProjectionDefinitionSpecification = string | ProjectionDefinitionT | PropertyValueSpecification<ProjectionDefinitionT>

export type PaddingSpecification = number | number[];
export type NumberArraySpecification = number | number[];
export type ColorArraySpecification = string | string[];

export type VariableAnchorOffsetCollectionSpecification = Array<string | [number, number]>;

export type SpriteSpecification = string | {id: string; url: string}[];

export type FormattedSpecification = string;

export type ResolvedImageSpecification = string;

export type PromoteIdSpecification = {[_: string]: string} | string;

export type ExpressionInputType = string | number | boolean;

export type VariableExpressionSpecification = ['var', string];

export type CollatorExpressionSpecification =
    ['collator', {
        'case-sensitive'?: boolean | ExpressionSpecification,
        'diacritic-sensitive'?: boolean | ExpressionSpecification,
        locale?: string | ExpressionSpecification}
    ]; // collator

export type InterpolationSpecification =
    | ['linear']
    | ['exponential', number]
    | ['cubic-bezier', number, number, number, number]

export type ExpressionSpecification =
    // types
    | ['array', ExpressionSpecification] // array
    | ['array', 'string' | 'number' | 'boolean', ExpressionSpecification] // array
    | ['array', 'string' | 'number' | 'boolean', number, ExpressionSpecification] // array
    | ['boolean', unknown | ExpressionSpecification, ...(unknown | ExpressionSpecification)[]] // boolean
    | CollatorExpressionSpecification
    | ['format', ...(string | ['image', ExpressionSpecification] | ExpressionSpecification | {'font-scale'?: number | ExpressionSpecification, 'text-font'?: ExpressionSpecification, 'text-color'?: ColorSpecification | ExpressionSpecification, 'vertical-align'?: 'bottom' | 'center' | 'top'})[]] // string
    | ['image', string | ExpressionSpecification] // image
    | ['literal', unknown]
    | ['semiliteral', unknown]
    | ['number', unknown | ExpressionSpecification, ...(unknown | ExpressionSpecification)[]] // number
    | ['number-format', number | ExpressionSpecification, {'locale'?: string | ExpressionSpecification, 'currency'?: string | ExpressionSpecification, 'min-fraction-digits'?: number | ExpressionSpecification, 'max-fraction-digits'?: number | ExpressionSpecification}] // string
    | ['number-format', number | ExpressionSpecification, {'locale'?: string | ExpressionSpecification, 'unit'?: string | ExpressionSpecification, 'min-fraction-digits'?: number | ExpressionSpecification, 'max-fraction-digits'?: number | ExpressionSpecification}] // string
    | ['object', unknown | ExpressionSpecification, ...(unknown | ExpressionSpecification)[]] // object
    | ['string', unknown | ExpressionSpecification, ...(unknown | ExpressionSpecification)[]] // string
    | ['to-boolean', unknown | ExpressionSpecification] // boolean
    | ['to-color', unknown | ExpressionSpecification, ...(unknown | ExpressionSpecification)[]] // color
    | ['to-number', unknown | ExpressionSpecification, ...(unknown | ExpressionSpecification)[]] // number
    | ['to-string', unknown | ExpressionSpecification] // string
    | ['typeof', unknown | ExpressionSpecification] // string
    // feature data
    | ['accumulated']
    | ['feature-state', string | ExpressionSpecification]
    | ['geometry-type'] // string
    | ['id']
    | ['line-progress'] // number
    | ['properties'] // object
    // lookup
    | ['at', number | ExpressionSpecification, ExpressionSpecification]
    | ['get', string | ExpressionSpecification, ExpressionSpecification?]
    | ['global-state', string]
    | ['has', string | ExpressionSpecification, ExpressionSpecification?]
    | ['in', null | ExpressionInputType | ExpressionSpecification, string | ExpressionSpecification]
    | ['index-of', null | ExpressionInputType | ExpressionSpecification, string | ExpressionSpecification, (number | ExpressionSpecification)?] // number
    | ['length', string | ExpressionSpecification]
    | ['slice', string | ExpressionSpecification, number | ExpressionSpecification, (number | ExpressionSpecification)?]
    // Decision
    | ['!', boolean | ExpressionSpecification] // boolean
    | ['!=', null | ExpressionInputType | ExpressionSpecification, null | ExpressionInputType | ExpressionSpecification, (CollatorExpressionSpecification | VariableExpressionSpecification)?] // boolean
    | ['<', string | number | ExpressionSpecification, string | number | ExpressionSpecification, (CollatorExpressionSpecification | VariableExpressionSpecification)?] // boolean
    | ['<=', string | number | ExpressionSpecification, string | number | ExpressionSpecification, (CollatorExpressionSpecification | VariableExpressionSpecification)?] // boolean
    | ['==', null | ExpressionInputType | ExpressionSpecification, null | ExpressionInputType | ExpressionSpecification, (CollatorExpressionSpecification | VariableExpressionSpecification)?] // boolean
    | ['>', string | number | ExpressionSpecification, string | number | ExpressionSpecification, (CollatorExpressionSpecification | VariableExpressionSpecification)?] // boolean
    | ['>=', string | number | ExpressionSpecification, string | number | ExpressionSpecification, (CollatorExpressionSpecification | VariableExpressionSpecification)?] // boolean
    | ['all', ...(boolean | ExpressionSpecification)[]] // boolean
    | ['any', ...(boolean | ExpressionSpecification)[]] // boolean
    | ['case', boolean | ExpressionSpecification, null | ExpressionInputType | ExpressionSpecification,
        ...(boolean | null | ExpressionInputType | ExpressionSpecification)[], null | ExpressionInputType | ExpressionSpecification]
    | ['coalesce', ...(ExpressionInputType | ExpressionSpecification)[]] // at least two inputs required
    | ['match', string | number | ExpressionSpecification,
        string | number | string[] | number[], null | ExpressionInputType | ExpressionSpecification,
        ...(string | number | string[] | number[] | null | ExpressionInputType | ExpressionSpecification)[], // repeated as above
        null | ExpressionInputType | ExpressionSpecification]
    | ['within', GeoJSON.GeoJSON]
    // Ramps, scales, curves
    | ['interpolate', InterpolationSpecification, number | ExpressionSpecification,
        ...(number | ColorSpecification | ExpressionSpecification | ProjectionDefinitionSpecification)[]] // alternating number and number | ColorSpecification | ExpressionSpecification | ProjectionDefinitionSpecification
    | ['interpolate-hcl', InterpolationSpecification, number | ExpressionSpecification,
        ...(number | ColorSpecification | ExpressionSpecification)[]] // alternating number and ColorSpecificaton | ExpressionSpecification
    | ['interpolate-lab', InterpolationSpecification, number | ExpressionSpecification,
        ...(number | ColorSpecification | ExpressionSpecification)[]] // alternating number and ColorSpecification | ExpressionSpecification
    | ['step', number | ExpressionSpecification, ExpressionInputType | ExpressionSpecification,
        ...(number | ExpressionInputType | ExpressionSpecification)[]] // alternating number and ExpressionInputType | ExpressionSpecification
    // Variable binding
    | ['let', string, ExpressionInputType | ExpressionSpecification, ...(string | ExpressionInputType | ExpressionSpecification)[]]
    | VariableExpressionSpecification
    // String
    | ['concat', ...(ExpressionInputType | ExpressionSpecification)[]] // at least two inputs required -> string
    | ['downcase', string | ExpressionSpecification] // string
    | ['is-supported-script', string | ExpressionSpecification] // boolean
    | ['join', string[] | ExpressionSpecification, string | ExpressionSpecification] // string
    | ['resolved-locale', CollatorExpressionSpecification] // string
    | ['split', string | ExpressionSpecification, string | ExpressionSpecification] // Array<string>
    | ['upcase', string | ExpressionSpecification] // string
    // Color
    | ['rgb', number | ExpressionSpecification, number | ExpressionSpecification, number | ExpressionSpecification] // color
    | ['rgba', number | ExpressionSpecification, number | ExpressionSpecification, number | ExpressionSpecification, number | ExpressionSpecification]
    | ['to-rgba', ColorSpecification | ExpressionSpecification]
    // Math
    | ['-', number | ExpressionSpecification, (number | ExpressionSpecification)?] // number
    | ['*', number | ExpressionSpecification, number | ExpressionSpecification, ...(number | ExpressionSpecification)[]] // number
    | ['/', number | ExpressionSpecification, number | ExpressionSpecification] // number
    | ['%', number | ExpressionSpecification, number | ExpressionSpecification] // number
    | ['^', number | ExpressionSpecification, number | ExpressionSpecification] // number
    | ['+', ...(number | ExpressionSpecification)[]] // at least two inputs required -> number
    | ['abs', number | ExpressionSpecification] // number
    | ['acos', number | ExpressionSpecification] // number
    | ['asin', number | ExpressionSpecification] // number
    | ['atan', number | ExpressionSpecification] // number
    | ['ceil', number | ExpressionSpecification] // number
    | ['cos', number | ExpressionSpecification] // number
    | ['distance', GeoJSON.GeoJSON] // number
    | ['e'] // number
    | ['floor', number | ExpressionSpecification] // number
    | ['ln', number | ExpressionSpecification] // number
    | ['ln2'] // number
    | ['log10', number | ExpressionSpecification] // number
    | ['log2', number | ExpressionSpecification] // number
    | ['max', number | ExpressionSpecification, ...(number | ExpressionSpecification)[]] // number
    | ['min', number | ExpressionSpecification, ...(number | ExpressionSpecification)[]] // number
    | ['pi'] // number
    | ['round', number | ExpressionSpecification] // number
    | ['sin', number | ExpressionSpecification] // number
    | ['sqrt', number | ExpressionSpecification] // number
    | ['tan', number | ExpressionSpecification] // number
    // Zoom
    | ['zoom'] // number
    // Heatmap
    | ['heatmap-density'] // number
    // Elevation
    | ['elevation'] // number
    // Global state
    | ['global-state', string] // unknown

export type ExpressionFilterSpecification = boolean | ExpressionSpecification

export type LegacyFilterSpecification =
    // Existential
    | ['has', string]
    | ['!has', string]
    // Comparison
    | ['==', string, string | number | boolean]
    | ['!=', string, string | number | boolean]
    | ['>', string, string | number | boolean]
    | ['>=', string, string | number | boolean]
    | ['<', string, string | number | boolean]
    | ['<=', string, string | number | boolean]
    // Set membership
    | ['in', string, ...(string | number | boolean)[]]
    | ['!in', string, ...(string | number | boolean)[]]
    // Combining
    | ['all', ...LegacyFilterSpecification[]]
    | ['any', ...LegacyFilterSpecification[]]
    | ['none', ...LegacyFilterSpecification[]]

export type FilterSpecification = ExpressionFilterSpecification | LegacyFilterSpecification

export type VisibilitySpecification = 'visible' | 'none' | ExpressionSpecification;

export type TransitionSpecification = {
    duration?: number,
    delay?: number
};

// Note: doesn't capture interpolatable vs. non-interpolatable types.

export type CameraFunctionSpecification<T> =
      { type: 'exponential', stops: Array<[number, T]> }
    | { type: 'interval',    stops: Array<[number, T]> };

export type SourceFunctionSpecification<T> =
      { type: 'exponential', stops: Array<[number, T]>, property: string, default?: T }
    | { type: 'interval',    stops: Array<[number, T]>, property: string, default?: T }
    | { type: 'categorical', stops: Array<[string | number | boolean, T]>, property: string, default?: T }
    | { type: 'identity', property: string, default?: T };

export type CompositeFunctionSpecification<T> =
      { type: 'exponential', stops: Array<[{zoom: number, value: number}, T]>, property: string, default?: T }
    | { type: 'interval',    stops: Array<[{zoom: number, value: number}, T]>, property: string, default?: T }
    | { type: 'categorical', stops: Array<[{zoom: number, value: string | number | boolean}, T]>, property: string, default?: T };

export type PropertyValueSpecification<T> =
      T
    | CameraFunctionSpecification<T>
    | ExpressionSpecification;

export type DataDrivenPropertyValueSpecification<T> =
      T
    | CameraFunctionSpecification<T>
    | SourceFunctionSpecification<T>
    | CompositeFunctionSpecification<T>
    | ExpressionSpecification;

export type SchemaSpecification = {
    default?: unknown
};

// State
export type StateSpecification = Record<string, SchemaSpecification>;

// Font faces
export type MLFontFace = {
    url: string,
    "unicode-range"?: string[]
};

export type FontFacesSpecification = Record<string, string | Array<MLFontFace>>;

export type StyleSpecification = {
    /**
     * Style specification version number. Must be 8.
     * 
     * @example
     * ```json
     * 8
     * ```
     */
    "version": 8,
    /**
     * A human-readable name for the style.
     * 
     * @example
     * ```json
     * "Bright"
     * ```
     */
    "name"?: string,
    /**
     * Arbitrary properties useful to track with the stylesheet, but do not influence rendering. Properties should be prefixed to avoid collisions, like 'maplibre:'.
     * 
     * @example
     * ```json
     * {
     *     "styleeditor:slimmode": true,
     *     "styleeditor:comment": "Style generated 1677776383",
     *     "styleeditor:version": "3.14.159265",
     *     "example:object": {
     *         "String": "one",
     *         "Number": 2,
     *         "Boolean": false
     *     }
     * }
     * ```
     */
    "metadata"?: unknown,
    /**
     * Default map center in longitude and latitude.  The style center will be used only if the map has not been positioned by other means (e.g. map options or user interaction).
     * 
     * @example
     * ```json
     * [-73.9749, 40.7736]
     * ```
     */
    "center"?: [number, number],
    /**
     * Default map center altitude in meters above sea level. The style center altitude defines the altitude where the camera is looking at and will be used only if the map has not been positioned by other means (e.g. map options or user interaction).
     * 
     * @example
     * ```json
     * 123.4
     * ```
     */
    "centerAltitude"?: number,
    /**
     * Default zoom level.  The style zoom will be used only if the map has not been positioned by other means (e.g. map options or user interaction).
     * 
     * @example
     * ```json
     * 12.5
     * ```
     */
    "zoom"?: number,
    /**
     * Default bearing, in degrees. The bearing is the compass direction that is "up"; for example, a bearing of 90° orients the map so that east is up. This value will be used only if the map has not been positioned by other means (e.g. map options or user interaction).
     * 
     * @example
     * ```json
     * 29
     * ```
     */
    "bearing"?: number,
    /**
     * Default pitch, in degrees. Zero is perpendicular to the surface, for a look straight down at the map, while a greater value like 60 looks ahead towards the horizon. The style pitch will be used only if the map has not been positioned by other means (e.g. map options or user interaction).
     * 
     * @example
     * ```json
     * 50
     * ```
     */
    "pitch"?: number,
    /**
     * Default roll, in degrees. The roll angle is measured counterclockwise about the camera boresight. The style roll will be used only if the map has not been positioned by other means (e.g. map options or user interaction).
     * 
     * @example
     * ```json
     * 45
     * ```
     */
    "roll"?: number,
    /**
     * An object used to define default values when using the [`global-state`](https://maplibre.org/maplibre-style-spec/expressions/#global-state) expression.
     * 
     * @default
     * ```json
     * {}
     * ```
     * 
     * @example
     * ```json
     * {
     *     "chargerType": {"default": ["CCS", "CHAdeMO", "Type2"]},
     *     "minPreferredChargingSpeed": {"default": 50}
     * }
     * ```
     */
    "state"?: StateSpecification,
    /**
     * The global light source.
     * 
     * @example
     * ```json
     * {"anchor": "viewport", "color": "white", "intensity": 0.4}
     * ```
     */
    "light"?: LightSpecification,
    /**
     * The map's sky configuration. **Note:** this definition is still experimental and is under development in maplibre-gl-js.
     * 
     * @example
     * ```json
     * {
     *     "sky-color": "#199EF3",
     *     "sky-horizon-blend": 0.5,
     *     "horizon-color": "#ffffff",
     *     "horizon-fog-blend": 0.5,
     *     "fog-color": "#0000ff",
     *     "fog-ground-blend": 0.5,
     *     "atmosphere-blend": [
     *         "interpolate",
     *         ["linear"],
     *         ["zoom"],
     *         0,
     *         1,
     *         10,
     *         1,
     *         12,
     *         0
     *     ]
     * }
     * ```
     */
    "sky"?: SkySpecification,
    /**
     * The projection configuration
     * 
     * @example
     * ```json
     * {
     *     "type": [
     *         "interpolate",
     *         ["linear"],
     *         ["zoom"],
     *         10,
     *         "vertical-perspective",
     *         12,
     *         "mercator"
     *     ]
     * }
     * ```
     */
    "projection"?: ProjectionSpecification,
    /**
     * The terrain configuration.
     * 
     * @example
     * ```json
     * {"source": "raster-dem-source", "exaggeration": 0.5}
     * ```
     */
    "terrain"?: TerrainSpecification,
    /**
     * Sources state which data the map should display. Specify the type of source with the `type` property. Adding a source isn't enough to make data appear on the map because sources don't contain styling details like color or width. Layers refer to a source and give it a visual representation. This makes it possible to style the same source in different ways, like differentiating between types of roads in a highways layer.
     * 
     * Tiled sources (vector and raster) must specify their details according to the [TileJSON specification](https://github.com/mapbox/tilejson-spec).
     * 
     * @example
     * ```json
     * {
     *     "maplibre-demotiles": {
     *         "type": "vector",
     *         "url": "https://demotiles.maplibre.org/tiles/tiles.json"
     *     },
     *     "maplibre-tilejson": {
     *         "type": "vector",
     *         "url": "http://api.example.com/tilejson.json"
     *     },
     *     "maplibre-streets": {
     *         "type": "vector",
     *         "tiles": [
     *             "http://a.example.com/tiles/{z}/{x}/{y}.pbf",
     *             "http://b.example.com/tiles/{z}/{x}/{y}.pbf"
     *         ],
     *         "maxzoom": 14
     *     },
     *     "wms-imagery": {
     *         "type": "raster",
     *         "tiles": [
     *             "http://a.example.com/wms?bbox={bbox-epsg-3857}&format=image/png&service=WMS&version=1.1.1&request=GetMap&srs=EPSG:3857&width=256&height=256&layers=example"
     *         ],
     *         "tileSize": 256
     *     }
     * }
     * ```
     */
    "sources": {[_: string]: SourceSpecification},
    /**
     * An array of `{id: 'my-sprite', url: 'https://example.com/sprite'}` objects. Each object should represent a unique URL to load a sprite from and and a unique ID to use as a prefix when referencing images from that sprite (i.e. 'my-sprite:image'). All the URLs are internally extended to load both .json and .png files. If the `id` field is equal to 'default', the prefix is omitted (just 'image' instead of 'default:image'). All the IDs and URLs must be unique. For backwards compatibility, instead of an array, one can also provide a single string that represent a URL to load the sprite from. The images in this case won't be prefixed.
     * 
     * @example
     * ```json
     * "https://demotiles.maplibre.org/styles/osm-bright-gl-style/sprite"
     * ```
     */
    "sprite"?: SpriteSpecification,
    /**
     * A URL template for loading signed-distance-field glyph sets in PBF format.
     * 
     * If this property is set, any text in the `text-field` layout property is displayed in the font stack named by the `text-font` layout property based on glyphs located at the URL specified by this property. Otherwise, font faces will be determined by the `text-font` property based on the local environment.
     * 
     * The URL must include:
     * 
     *  - `{fontstack}` - When requesting glyphs, this token is replaced with a comma separated list of fonts from a font stack specified in the `text-font` property of a symbol layer. 
     * 
     *  - `{range}` - When requesting glyphs, this token is replaced with a range of 256 Unicode code points. For example, to load glyphs for the Unicode Basic Latin and Basic Latin-1 Supplement blocks, the range would be 0-255. The actual ranges that are loaded are determined at runtime based on what text needs to be displayed.
     * 
     * The URL must be absolute, containing the [scheme, authority and path components](https://en.wikipedia.org/wiki/URL#Syntax).
     * 
     * @example
     * ```json
     * "https://demotiles.maplibre.org/font/{fontstack}/{range}.pbf"
     * ```
     */
    "glyphs"?: string,
    /**
     * The `font-faces` property can be used to specify what font files to use for rendering text. Font faces contain information needed to render complex texts such as [Devanagari](https://en.wikipedia.org/wiki/Devanagari), [Khmer](https://en.wikipedia.org/wiki/Khmer_script) among many others.<h2>Unicode range</h2>The optional `unicode-range` property can be used to only use a particular font file for characters within the specified unicode range(s). Its value should be an array of strings, each indicating a start and end of a unicode range, similar to the [CSS descriptor with the same name](https://developer.mozilla.org/en-US/docs/Web/CSS/@font-face/unicode-range). This allows specifying multiple non-consecutive unicode ranges. When not specified, the default value is `U+0-10FFFF`, meaning the font file will be used for all unicode characters.
     * 
     * Refer to the [Unicode Character Code Charts](https://www.unicode.org/charts/) to see ranges for scripts supported by Unicode. To see what unicode code-points are available in a font, use a tool like [FontDrop](https://fontdrop.info/).
     * 
     * <h2>Font Resolution</h2>For every name in a symbol layer’s [`text-font`](./layers.md#text-font) array, characters are matched if they are covered one of the by the font files in the corresponding entry of the `font-faces` map. Any still-unmatched characters then fall back to the [`glyphs`](./glyphs.md) URL if provided.
     * 
     * <h2>Supported Fonts</h2>What type of fonts are supported is implementation-defined. Unsupported fonts are ignored.
     * 
     * @example
     * ```json
     * {
     *     "Noto Sans Regular": [
     *         {
     *             "url": "https://cdn.jsdelivr.net/gh/notofonts/notofonts.github.io/fonts/NotoSansKhmer/hinted/ttf/NotoSansKhmer-Regular.ttf",
     *             "unicode-range": ["U+1780-17FF"]
     *         },
     *         {
     *             "url": "https://cdn.jsdelivr.net/gh/notofonts/notofonts.github.io/fonts/NotoSansDevanagari/hinted/ttf/NotoSansDevanagari-Regular.ttf",
     *             "unicode-range": ["U+0900-097F"]
     *         },
     *         {
     *             "url": "https://cdn.jsdelivr.net/gh/notofonts/notofonts.github.io/fonts/NotoSansMyanmar/hinted/ttf/NotoSansMyanmar-Regular.ttf",
     *             "unicode-range": ["U+1000-109F"]
     *         },
     *         {
     *             "url": "https://cdn.jsdelivr.net/gh/notofonts/notofonts.github.io/fonts/NotoSansEthiopic/hinted/ttf/NotoSansEthiopic-Regular.ttf",
     *             "unicode-range": ["U+1200-137F"]
     *         }
     *     ],
     *     "Unifont": "https://ftp.gnu.org/gnu/unifont/unifont-15.0.01/unifont-15.0.01.ttf"
     * }
     * ```
     */
    "font-faces"?: FontFacesSpecification,
    /**
     * A global transition definition to use as a default across properties, to be used for timing transitions between one value and the next when no property-specific transition is set. Collision-based symbol fading is controlled independently of the style's `transition` property.
     * 
     * In addition to this global definition via `transition`, if any individual paint or layout property are marked as `Transitionable`, a corresponding `*-transition` property is avaliable to fine-tune the property’s animation between old and new values based on similar `duration` and `delay` values.
     * 
     * For example, [`fill-color`](layers/#fill-color) is marked as `Transitionable`, so it can transition either independently via `fill-color-transition` or globally via the style's `transition` property:
     * 
     * @example
     * ```json
     * {"duration": 300, "delay": 0}
     * ```
     */
    "transition"?: TransitionSpecification,
    /**
     * A style's `layers` property lists all the layers available in that style. The type of layer is specified by the `type` property, and must be one of `background`, `fill`, `line`, `symbol`, `raster`, `circle`, `fill-extrusion`, `heatmap`, `hillshade`, `color-relief`.
     * 
     * Except for layers of the `background` type, each layer needs to refer to a source. Layers take the data that they get from a source, optionally filter features, and then define how those features are styled.
     * 
     * @example
     * ```json
     * [
     *     {
     *         "id": "coastline",
     *         "source": "maplibre",
     *         "source-layer": "countries",
     *         "type": "line",
     *         "paint": {"line-color": "#198EC8"}
     *     }
     * ]
     * ```
     */
    "layers": Array<LayerSpecification>
};

export type LightSpecification = {
    /**
     * Whether extruded geometries are lit relative to the map or viewport.
     * 
     * @default
     * ```json
     * "viewport"
     * ```
     * 
     * @example
     * ```json
     * "map"
     * ```
     */
    "anchor"?: PropertyValueSpecification<"map" | "viewport">,
    /**
     * Position of the light source relative to lit (extruded) geometries, in `[r radial coordinate, a azimuthal angle, p polar angle]` where r indicates the distance from the center of the base of an object to its light, a indicates the position of the light relative to 0° (0° when `light.anchor` is set to `viewport` corresponds to the top of the viewport, or 0° when `light.anchor` is set to `map` corresponds to due north, and degrees proceed clockwise), and p indicates the height of the light (from 0°, directly above, to 180°, directly below).
     * 
     * @default
     * ```json
     * [1.15, 210, 30]
     * ```
     * 
     * @example
     * ```json
     * [1.5, 90, 80]
     * ```
     */
    "position"?: PropertyValueSpecification<[number, number, number]>,
    "position-transition"?: TransitionSpecification,
    /**
     * Color tint for lighting extruded geometries.
     * 
     * @default
     * ```json
     * "#ffffff"
     * ```
     */
    "color"?: PropertyValueSpecification<ColorSpecification>,
    "color-transition"?: TransitionSpecification,
    /**
     * Intensity of lighting (on a scale from 0 to 1). Higher numbers will present as more extreme contrast.
     * 
     * @default
     * ```json
     * 0.5
     * ```
     */
    "intensity"?: PropertyValueSpecification<number>,
    "intensity-transition"?: TransitionSpecification
};

export type SkySpecification = {
    /**
     * The base color for the sky.
     * 
     * @default
     * ```json
     * "#88C6FC"
     * ```
     */
    "sky-color"?: PropertyValueSpecification<ColorSpecification>,
    "sky-color-transition"?: TransitionSpecification,
    /**
     * The base color at the horizon.
     * 
     * @default
     * ```json
     * "#ffffff"
     * ```
     */
    "horizon-color"?: PropertyValueSpecification<ColorSpecification>,
    "horizon-color-transition"?: TransitionSpecification,
    /**
     * The base color for the fog. Requires 3D terrain.
     * 
     * @default
     * ```json
     * "#ffffff"
     * ```
     */
    "fog-color"?: PropertyValueSpecification<ColorSpecification>,
    "fog-color-transition"?: TransitionSpecification,
    /**
     * How to blend the fog over the 3D terrain. Where 0 is the map center and 1 is the horizon.
     * 
     * @default
     * ```json
     * 0.5
     * ```
     */
    "fog-ground-blend"?: PropertyValueSpecification<number>,
    "fog-ground-blend-transition"?: TransitionSpecification,
    /**
     * How to blend the fog color and the horizon color. Where 0 is using the horizon color only and 1 is using the fog color only.
     * 
     * @default
     * ```json
     * 0.8
     * ```
     */
    "horizon-fog-blend"?: PropertyValueSpecification<number>,
    "horizon-fog-blend-transition"?: TransitionSpecification,
    /**
     * How to blend the sky color and the horizon color. Where 1 is blending the color at the middle of the sky and 0 is not blending at all and using the sky color only.
     * 
     * @default
     * ```json
     * 0.8
     * ```
     */
    "sky-horizon-blend"?: PropertyValueSpecification<number>,
    "sky-horizon-blend-transition"?: TransitionSpecification,
    /**
     * How to blend the atmosphere. Where 1 is visible atmosphere and 0 is hidden. It is best to interpolate this expression when using globe projection.
     * 
     * @default
     * ```json
     * 0.8
     * ```
     */
    "atmosphere-blend"?: PropertyValueSpecification<number>,
    "atmosphere-blend-transition"?: TransitionSpecification
};

export type ProjectionSpecification = {
    /**
     * The projection definition type. Can be specified as a string, a transition state, or an expression.
     * 
     * @default
     * ```json
     * "mercator"
     * ```
     */
    "type"?: PropertyValueSpecification<ProjectionDefinitionSpecification>
};

export type TerrainSpecification = {
    /**
     * The source for the terrain data.
     */
    "source": string,
    /**
     * The exaggeration of the terrain - how high it will look.
     * 
     * @default
     * ```json
     * 1
     * ```
     */
    "exaggeration"?: number
};

export type VectorSourceSpecification = {
    /**
     * The type of the source.
     */
    "type": "vector",
    /**
     * A URL to a TileJSON resource. Supported protocols are `http:` and `https:`.
     */
    "url"?: string,
    /**
     * An array of one or more tile source URLs, as in the TileJSON spec.
     */
    "tiles"?: Array<string>,
    /**
     * An array containing the longitude and latitude of the southwest and northeast corners of the source's bounding box in the following order: `[sw.lng, sw.lat, ne.lng, ne.lat]`. When this property is included in a source, no tiles outside of the given bounds are requested by MapLibre.
     * 
     * @default
     * ```json
     * [-180, -85.051129, 180, 85.051129]
     * ```
     */
    "bounds"?: [number, number, number, number],
    /**
     * Influences the y direction of the tile coordinates. The global-mercator (aka Spherical Mercator) profile is assumed.
     * 
     * @default
     * ```json
     * "xyz"
     * ```
     */
    "scheme"?: "xyz" | "tms",
    /**
     * Minimum zoom level for which tiles are available, as in the TileJSON spec.
     */
    "minzoom"?: number,
    /**
     * Maximum zoom level for which tiles are available, as in the TileJSON spec. Data from tiles at the maxzoom are used when displaying the map at higher zoom levels.
     * 
     * @default
     * ```json
     * 22
     * ```
     */
    "maxzoom"?: number,
    /**
     * Contains an attribution to be displayed when the map is shown to a user.
     */
    "attribution"?: string,
    /**
     * A property to use as a feature id (for feature state). Either a property name, or an object of the form `{<sourceLayer>: <propertyName>}`. If specified as a string for a vector tile source, the same property is used across all its source layers.
     */
    "promoteId"?: PromoteIdSpecification,
    /**
     * A setting to determine whether a source's tiles are cached locally.
     */
    "volatile"?: boolean,
    /**
     * The encoding used by this source. Mapbox Vector Tiles encoding is used by default.
     * 
     * @default
     * ```json
     * "mvt"
     * ```
     */
    "encoding"?: "mvt" | "mlt"
};

export type RasterSourceSpecification = {
    /**
     * The type of the source.
     */
    "type": "raster",
    /**
     * A URL to a TileJSON resource. Supported protocols are `http:` and `https:`.
     */
    "url"?: string,
    /**
     * An array of one or more tile source URLs, as in the TileJSON spec.
     */
    "tiles"?: Array<string>,
    /**
     * An array containing the longitude and latitude of the southwest and northeast corners of the source's bounding box in the following order: `[sw.lng, sw.lat, ne.lng, ne.lat]`. When this property is included in a source, no tiles outside of the given bounds are requested by MapLibre.
     * 
     * @default
     * ```json
     * [-180, -85.051129, 180, 85.051129]
     * ```
     */
    "bounds"?: [number, number, number, number],
    /**
     * Minimum zoom level for which tiles are available, as in the TileJSON spec.
     */
    "minzoom"?: number,
    /**
     * Maximum zoom level for which tiles are available, as in the TileJSON spec. Data from tiles at the maxzoom are used when displaying the map at higher zoom levels.
     * 
     * @default
     * ```json
     * 22
     * ```
     */
    "maxzoom"?: number,
    /**
     * The minimum visual size to display tiles for this layer. Only configurable for raster layers.
     * 
     * @default
     * ```json
     * 512
     * ```
     */
    "tileSize"?: number,
    /**
     * Influences the y direction of the tile coordinates. The global-mercator (aka Spherical Mercator) profile is assumed.
     * 
     * @default
     * ```json
     * "xyz"
     * ```
     */
    "scheme"?: "xyz" | "tms",
    /**
     * Contains an attribution to be displayed when the map is shown to a user.
     */
    "attribution"?: string,
    /**
     * A setting to determine whether a source's tiles are cached locally.
     */
    "volatile"?: boolean
};

export type RasterDEMSourceSpecification = {
    /**
     * The type of the source.
     */
    "type": "raster-dem",
    /**
     * A URL to a TileJSON resource. Supported protocols are `http:` and `https:`.
     */
    "url"?: string,
    /**
     * An array of one or more tile source URLs, as in the TileJSON spec.
     */
    "tiles"?: Array<string>,
    /**
     * An array containing the longitude and latitude of the southwest and northeast corners of the source's bounding box in the following order: `[sw.lng, sw.lat, ne.lng, ne.lat]`. When this property is included in a source, no tiles outside of the given bounds are requested by MapLibre.
     * 
     * @default
     * ```json
     * [-180, -85.051129, 180, 85.051129]
     * ```
     */
    "bounds"?: [number, number, number, number],
    /**
     * Minimum zoom level for which tiles are available, as in the TileJSON spec.
     */
    "minzoom"?: number,
    /**
     * Maximum zoom level for which tiles are available, as in the TileJSON spec. Data from tiles at the maxzoom are used when displaying the map at higher zoom levels.
     * 
     * @default
     * ```json
     * 22
     * ```
     */
    "maxzoom"?: number,
    /**
     * The minimum visual size to display tiles for this layer. Only configurable for raster layers.
     * 
     * @default
     * ```json
     * 512
     * ```
     */
    "tileSize"?: number,
    /**
     * Contains an attribution to be displayed when the map is shown to a user.
     */
    "attribution"?: string,
    /**
     * The encoding used by this source. Mapbox Terrain RGB is used by default.
     * 
     * @default
     * ```json
     * "mapbox"
     * ```
     */
    "encoding"?: "terrarium" | "mapbox" | "custom",
    /**
     * Value that will be multiplied by the red channel value when decoding. Only used on custom encodings.
     * 
     * @default
     * ```json
     * 1
     * ```
     */
    "redFactor"?: number,
    /**
     * Value that will be multiplied by the blue channel value when decoding. Only used on custom encodings.
     * 
     * @default
     * ```json
     * 1
     * ```
     */
    "blueFactor"?: number,
    /**
     * Value that will be multiplied by the green channel value when decoding. Only used on custom encodings.
     * 
     * @default
     * ```json
     * 1
     * ```
     */
    "greenFactor"?: number,
    /**
     * Value that will be added to the encoding mix when decoding. Only used on custom encodings.
     */
    "baseShift"?: number,
    /**
     * A setting to determine whether a source's tiles are cached locally.
     */
    "volatile"?: boolean
};

export type GeoJSONSourceSpecification = {
    /**
     * The data type of the GeoJSON source.
     */
    "type": "geojson",
    /**
     * A URL to a GeoJSON file, or inline GeoJSON.
     */
    "data": GeoJSON.GeoJSON | string,
    /**
     * Maximum zoom level at which to create vector tiles (higher means greater detail at high zoom levels).
     * 
     * @default
     * ```json
     * 18
     * ```
     */
    "maxzoom"?: number,
    /**
     * Contains an attribution to be displayed when the map is shown to a user.
     */
    "attribution"?: string,
    /**
     * Size of the tile buffer on each side. A value of 0 produces no buffer. A value of 512 produces a buffer as wide as the tile itself. Larger values produce fewer rendering artifacts near tile edges and slower performance.
     * 
     * @default
     * ```json
     * 128
     * ```
     */
    "buffer"?: number,
    /**
     * An expression for filtering features prior to processing them for rendering.
     */
    "filter"?: FilterSpecification,
    /**
     * Douglas-Peucker simplification tolerance (higher means simpler geometries and faster performance).
     * 
     * @default
     * ```json
     * 0.375
     * ```
     */
    "tolerance"?: number,
    /**
     * If the data is a collection of point features, setting this to true clusters the points by radius into groups. Cluster groups become new `Point` features in the source with additional properties:
     * 
     *  * `cluster` Is `true` if the point is a cluster 
     * 
     *  * `cluster_id` A unique id for the cluster to be used in conjunction with the [cluster inspection methods](https://maplibre.org/maplibre-gl-js/docs/API/classes/GeoJSONSource/#getclusterexpansionzoom)
     * 
     *  * `point_count` Number of original points grouped into this cluster
     * 
     *  * `point_count_abbreviated` An abbreviated point count
     */
    "cluster"?: boolean,
    /**
     * Radius of each cluster if clustering is enabled. A value of 512 indicates a radius equal to the width of a tile.
     * 
     * @default
     * ```json
     * 50
     * ```
     */
    "clusterRadius"?: number,
    /**
     * Max zoom on which to cluster points if clustering is enabled. Defaults to one zoom less than maxzoom (so that last zoom features are not clustered). Clusters are re-evaluated at integer zoom levels so setting clusterMaxZoom to 14 means the clusters will be displayed until z15.
     */
    "clusterMaxZoom"?: number,
    /**
     * Minimum number of points necessary to form a cluster if clustering is enabled. Defaults to `2`.
     */
    "clusterMinPoints"?: number,
    /**
     * An object defining custom properties on the generated clusters if clustering is enabled, aggregating values from clustered points. Has the form `{"property_name": [operator, map_expression]}`. `operator` is any expression function that accepts at least 2 operands (e.g. `"+"` or `"max"`) - it accumulates the property value from clusters/points the cluster contains; `map_expression` produces the value of a single point.
     * 
     * Example: `{"sum": ["+", ["get", "scalerank"]]}`.
     * 
     * For more advanced use cases, in place of `operator`, you can use a custom reduce expression that references a special `["accumulated"]` value, e.g.:
     * 
     * `{"sum": [["+", ["accumulated"], ["get", "sum"]], ["get", "scalerank"]]}`
     */
    "clusterProperties"?: unknown,
    /**
     * Whether to calculate line distance metrics. This is required for line layers that specify `line-gradient` values.
     */
    "lineMetrics"?: boolean,
    /**
     * Whether to generate ids for the geojson features. When enabled, the `feature.id` property will be auto assigned based on its index in the `features` array, over-writing any previous values.
     */
    "generateId"?: boolean,
    /**
     * A property to use as a feature id (for feature state). Either a property name, or an object of the form `{<sourceLayer>: <propertyName>}`.
     */
    "promoteId"?: PromoteIdSpecification
};

export type VideoSourceSpecification = {
    /**
     * The data type of the video source.
     */
    "type": "video",
    /**
     * URLs to video content in order of preferred format.
     */
    "urls": Array<string>,
    /**
     * Corners of video specified in longitude, latitude pairs.
     */
    "coordinates": [[number, number], [number, number], [number, number], [number, number]]
};

export type ImageSourceSpecification = {
    /**
     * The data type of the image source.
     */
    "type": "image",
    /**
     * URL that points to an image. Optional: a source created without a url starts empty and renders nothing until an image is set at runtime.
     */
    "url"?: string,
    /**
     * Corners of image specified in longitude, latitude pairs.
     */
    "coordinates": [[number, number], [number, number], [number, number], [number, number]]
};

export type SourceSpecification =
    | VectorSourceSpecification
    | RasterSourceSpecification
    | RasterDEMSourceSpecification
    | GeoJSONSourceSpecification
    | VideoSourceSpecification
    | ImageSourceSpecification

export type FillLayerSpecification = {
    /**
     * Unique layer name.
     */
    "id": string,
    "type": "fill",
    /**
     * Arbitrary properties useful to track with the layer, but do not influence rendering. Properties should be prefixed to avoid collisions, like 'maplibre:'.
     * 
     * @example
     * ```json
     * {"source:comment": "Hydrology FCCODE 460 - Narrow wash"}
     * ```
     */
    "metadata"?: unknown,
    /**
     * Name of a source description to be used for this layer. Required for all layer types except `background`.
     */
    "source": string,
    /**
     * Layer to use from a vector tile source. Required for vector tile sources; prohibited for all other source types, including GeoJSON sources.
     */
    "source-layer"?: string,
    /**
     * The minimum zoom level for the layer. At zoom levels less than the minzoom, the layer will be hidden.
     */
    "minzoom"?: number,
    /**
     * The maximum zoom level for the layer. At zoom levels equal to or greater than the maxzoom, the layer will be hidden.
     */
    "maxzoom"?: number,
    /**
     * A expression specifying conditions on source features. Only features that match the filter are displayed. Zoom expressions in filters are only evaluated at integer zoom levels. The `feature-state` expression is not supported in filter expressions.
     */
    "filter"?: FilterSpecification,
    /**
     * Layout properties for the layer.
     */
    "layout"?: {
            /**
             * Sorts features in ascending order based on this value. Features with a higher sort key will appear above features with a lower sort key.
             */
            "fill-sort-key"?: DataDrivenPropertyValueSpecification<number>,
            /**
             * Whether this layer is displayed.
             * 
             * @default
             * ```json
             * "visible"
             * ```
             */
            "visibility"?: VisibilitySpecification
        },
    /**
     * Default paint properties for this layer.
     */
    "paint"?: {
            /**
             * Whether or not the fill should be antialiased.
             * 
             * @default
             * ```json
             * true
             * ```
             */
            "fill-antialias"?: PropertyValueSpecification<boolean>,
            /**
             * The opacity of the entire fill layer. In contrast to the `fill-color`, this value will also affect the 1px stroke around the fill, if the stroke is used.
             * 
             * @default
             * ```json
             * 1
             * ```
             */
            "fill-opacity"?: DataDrivenPropertyValueSpecification<number>,
            "fill-opacity-transition"?: TransitionSpecification,
            /**
             * Opacity applied to the layer as a whole. Unlike `fill-opacity` and alpha values in `fill-color`, which are applied per feature and accumulate where fills overlap, `fill-layer-opacity` is applied once so overlapping fills appear as a single surface at the given opacity. When both `fill-opacity` and `fill-layer-opacity` are set, the per-feature, overlap accumulation is preserved, then `fill-layer-opacity` composites the result. This property affects only the layer it is set on and cannot be used to composite multiple layers together or control how this layer blends with layers above or below it.
             * 
             * ![fill-opacity vs. fill-layer-opacity](assets/fill-layer-opacity.svg)
             * 
             * @default
             * ```json
             * 1
             * ```
             */
            "fill-layer-opacity"?: PropertyValueSpecification<number>,
            "fill-layer-opacity-transition"?: TransitionSpecification,
            /**
             * The color of the filled part of this layer. This color can be specified as `rgba` with an alpha component and the color's opacity will not affect the opacity of the 1px stroke, if it is used. When used with an SDF fill pattern, this serves as the foreground color of the pattern.
             * 
             * @default
             * ```json
             * "#000000"
             * ```
             */
            "fill-color"?: DataDrivenPropertyValueSpecification<ColorSpecification>,
            "fill-color-transition"?: TransitionSpecification,
            /**
             * The outline color of the fill. Matches the value of `fill-color` if unspecified.
             */
            "fill-outline-color"?: DataDrivenPropertyValueSpecification<ColorSpecification>,
            "fill-outline-color-transition"?: TransitionSpecification,
            /**
             * The geometry's offset. Values are `[x, y]` where negatives indicate left and up, respectively.
             * 
             * @default
             * ```json
             * [0, 0]
             * ```
             */
            "fill-translate"?: PropertyValueSpecification<[number, number]>,
            "fill-translate-transition"?: TransitionSpecification,
            /**
             * Controls the frame of reference for `fill-translate`.
             * 
             * @default
             * ```json
             * "map"
             * ```
             */
            "fill-translate-anchor"?: PropertyValueSpecification<"map" | "viewport">,
            /**
             * Name of image in sprite to use for drawing image fills. For seamless patterns, image width and height must be a factor of two (2, 4, 8, ..., 512). Note that zoom-dependent expressions will be evaluated only at integer zoom levels.
             */
            "fill-pattern"?: DataDrivenPropertyValueSpecification<ResolvedImageSpecification>,
            "fill-pattern-transition"?: TransitionSpecification
        }
};

export type LineLayerSpecification = {
    /**
     * Unique layer name.
     */
    "id": string,
    "type": "line",
    /**
     * Arbitrary properties useful to track with the layer, but do not influence rendering. Properties should be prefixed to avoid collisions, like 'maplibre:'.
     * 
     * @example
     * ```json
     * {"source:comment": "Hydrology FCCODE 460 - Narrow wash"}
     * ```
     */
    "metadata"?: unknown,
    /**
     * Name of a source description to be used for this layer. Required for all layer types except `background`.
     */
    "source": string,
    /**
     * Layer to use from a vector tile source. Required for vector tile sources; prohibited for all other source types, including GeoJSON sources.
     */
    "source-layer"?: string,
    /**
     * The minimum zoom level for the layer. At zoom levels less than the minzoom, the layer will be hidden.
     */
    "minzoom"?: number,
    /**
     * The maximum zoom level for the layer. At zoom levels equal to or greater than the maxzoom, the layer will be hidden.
     */
    "maxzoom"?: number,
    /**
     * A expression specifying conditions on source features. Only features that match the filter are displayed. Zoom expressions in filters are only evaluated at integer zoom levels. The `feature-state` expression is not supported in filter expressions.
     */
    "filter"?: FilterSpecification,
    /**
     * Layout properties for the layer.
     */
    "layout"?: {
            /**
             * The display of line endings.
             * 
             * @default
             * ```json
             * "butt"
             * ```
             */
            "line-cap"?: DataDrivenPropertyValueSpecification<"butt" | "round" | "square">,
            /**
             * The display of lines when joining.
             * 
             * @default
             * ```json
             * "miter"
             * ```
             */
            "line-join"?: DataDrivenPropertyValueSpecification<"bevel" | "round" | "miter">,
            /**
             * Used to automatically convert miter joins to bevel joins for sharp angles.
             * 
             * @default
             * ```json
             * 2
             * ```
             */
            "line-miter-limit"?: DataDrivenPropertyValueSpecification<number>,
            /**
             * Used to automatically convert round joins to miter joins for shallow angles.
             * 
             * @default
             * ```json
             * 1.05
             * ```
             */
            "line-round-limit"?: DataDrivenPropertyValueSpecification<number>,
            /**
             * Sorts features in ascending order based on this value. Features with a higher sort key will appear above features with a lower sort key.
             */
            "line-sort-key"?: DataDrivenPropertyValueSpecification<number>,
            /**
             * Whether this layer is displayed.
             * 
             * @default
             * ```json
             * "visible"
             * ```
             */
            "visibility"?: VisibilitySpecification
        },
    /**
     * Default paint properties for this layer.
     */
    "paint"?: {
            /**
             * The opacity at which the line will be drawn.
             * 
             * @default
             * ```json
             * 1
             * ```
             */
            "line-opacity"?: DataDrivenPropertyValueSpecification<number>,
            "line-opacity-transition"?: TransitionSpecification,
            /**
             * Opacity applied to the layer as a whole. Unlike `line-opacity` and alpha values in `line-color`, which are applied per feature and accumulate where lines overlap, `line-layer-opacity` is applied once so overlapping lines appear as a single surface at the given opacity. When both `line-opacity` and `line-layer-opacity` are set, the per-feature, overlap accumulation is preserved, then layer-opacity composites the result. This property affects only the layer it is set on and cannot be used to composite multiple layers together or control how this layer blends with layers above or below it.
             * 
             * ![line-opacity vs. line-layer-opacity](assets/line-layer-opacity.svg)
             * 
             * @default
             * ```json
             * 1
             * ```
             */
            "line-layer-opacity"?: PropertyValueSpecification<number>,
            "line-layer-opacity-transition"?: TransitionSpecification,
            /**
             * The color with which the line will be drawn.
             * 
             * @default
             * ```json
             * "#000000"
             * ```
             */
            "line-color"?: DataDrivenPropertyValueSpecification<ColorSpecification>,
            "line-color-transition"?: TransitionSpecification,
            /**
             * The geometry's offset. Values are `[x, y]` where negatives indicate left and up, respectively.
             * 
             * @default
             * ```json
             * [0, 0]
             * ```
             */
            "line-translate"?: PropertyValueSpecification<[number, number]>,
            "line-translate-transition"?: TransitionSpecification,
            /**
             * Controls the frame of reference for `line-translate`.
             * 
             * @default
             * ```json
             * "map"
             * ```
             */
            "line-translate-anchor"?: PropertyValueSpecification<"map" | "viewport">,
            /**
             * Stroke thickness.
             * 
             * @default
             * ```json
             * 1
             * ```
             */
            "line-width"?: DataDrivenPropertyValueSpecification<number>,
            "line-width-transition"?: TransitionSpecification,
            /**
             * Draws a line casing outside of a line's actual path. Value indicates the width of the inner gap.
             */
            "line-gap-width"?: DataDrivenPropertyValueSpecification<number>,
            "line-gap-width-transition"?: TransitionSpecification,
            /**
             * The line's offset. For linear features, a positive value offsets the line to the right, relative to the direction of the line, and a negative value to the left. For polygon features, a positive value results in an inset, and a negative value results in an outset.
             */
            "line-offset"?: DataDrivenPropertyValueSpecification<number>,
            "line-offset-transition"?: TransitionSpecification,
            /**
             * Blur applied to the line, in pixels.
             */
            "line-blur"?: DataDrivenPropertyValueSpecification<number>,
            "line-blur-transition"?: TransitionSpecification,
            /**
             * Specifies the lengths of the alternating dashes and gaps that form the dash pattern. The lengths are later scaled by the line width. To convert a dash length to pixels, multiply the length by the current line width. GeoJSON sources with `lineMetrics: true` specified won't render dashed lines to the expected scale. Zoom-dependent expressions will be evaluated only at integer zoom levels. The only way to create an array value is using `["literal", [...]]`; arrays cannot be read from or derived from feature properties.
             */
            "line-dasharray"?: DataDrivenPropertyValueSpecification<Array<number>>,
            "line-dasharray-transition"?: TransitionSpecification,
            /**
             * Name of image in sprite to use for drawing image lines. For seamless patterns, image width must be a factor of two (2, 4, 8, ..., 512). Note that zoom-dependent expressions will be evaluated only at integer zoom levels.
             */
            "line-pattern"?: DataDrivenPropertyValueSpecification<ResolvedImageSpecification>,
            "line-pattern-transition"?: TransitionSpecification,
            /**
             * Defines a gradient with which to color a line feature. Can only be used with GeoJSON sources that specify `"lineMetrics": true`.
             */
            "line-gradient"?: ExpressionSpecification
        }
};

export type SymbolLayerSpecification = {
    /**
     * Unique layer name.
     */
    "id": string,
    "type": "symbol",
    /**
     * Arbitrary properties useful to track with the layer, but do not influence rendering. Properties should be prefixed to avoid collisions, like 'maplibre:'.
     * 
     * @example
     * ```json
     * {"source:comment": "Hydrology FCCODE 460 - Narrow wash"}
     * ```
     */
    "metadata"?: unknown,
    /**
     * Name of a source description to be used for this layer. Required for all layer types except `background`.
     */
    "source": string,
    /**
     * Layer to use from a vector tile source. Required for vector tile sources; prohibited for all other source types, including GeoJSON sources.
     */
    "source-layer"?: string,
    /**
     * The minimum zoom level for the layer. At zoom levels less than the minzoom, the layer will be hidden.
     */
    "minzoom"?: number,
    /**
     * The maximum zoom level for the layer. At zoom levels equal to or greater than the maxzoom, the layer will be hidden.
     */
    "maxzoom"?: number,
    /**
     * A expression specifying conditions on source features. Only features that match the filter are displayed. Zoom expressions in filters are only evaluated at integer zoom levels. The `feature-state` expression is not supported in filter expressions.
     */
    "filter"?: FilterSpecification,
    /**
     * Layout properties for the layer.
     */
    "layout"?: {
            /**
             * Label placement relative to its geometry.
             * 
             * @default
             * ```json
             * "point"
             * ```
             */
            "symbol-placement"?: PropertyValueSpecification<"point" | "line" | "line-center">,
            /**
             * Distance between two symbol anchors.
             * 
             * @default
             * ```json
             * 250
             * ```
             */
            "symbol-spacing"?: PropertyValueSpecification<number>,
            /**
             * If true, the symbols will not cross tile edges to avoid mutual collisions. Recommended in layers that don't have enough padding in the vector tile to prevent collisions, or if it is a point symbol layer placed after a line symbol layer. When using a client that supports global collision detection, like MapLibre GL JS version 0.42.0 or greater, enabling this property is not needed to prevent clipped labels at tile boundaries.
             */
            "symbol-avoid-edges"?: PropertyValueSpecification<boolean>,
            /**
             * Sorts features in ascending order based on this value. Features with lower sort keys are drawn and placed first.  When `icon-allow-overlap` or `text-allow-overlap` is `false`, features with a lower sort key will have priority during placement. When `icon-allow-overlap` or `text-allow-overlap` is set to `true`, features with a higher sort key will overlap over features with a lower sort key.
             */
            "symbol-sort-key"?: DataDrivenPropertyValueSpecification<number>,
            /**
             * Determines whether overlapping symbols in the same layer are rendered in the order that they appear in the data source or by their y-position relative to the viewport. To control the order and prioritization of symbols otherwise, use `symbol-sort-key`.
             * 
             * @default
             * ```json
             * "auto"
             * ```
             */
            "symbol-z-order"?: PropertyValueSpecification<"auto" | "viewport-y" | "source">,
            /**
             * If true, the icon will be visible even if it collides with other previously drawn symbols.
             */
            "icon-allow-overlap"?: PropertyValueSpecification<boolean>,
            /**
             * Allows for control over whether to show an icon when it overlaps other symbols on the map. If `icon-overlap` is not set, `icon-allow-overlap` is used instead.
             */
            "icon-overlap"?: PropertyValueSpecification<"never" | "always" | "cooperative">,
            /**
             * If true, other symbols can be visible even if they collide with the icon.
             */
            "icon-ignore-placement"?: PropertyValueSpecification<boolean>,
            /**
             * If true, text will display without their corresponding icons when the icon collides with other symbols and the text does not.
             */
            "icon-optional"?: PropertyValueSpecification<boolean>,
            /**
             * In combination with `symbol-placement`, determines the rotation behavior of icons.
             * 
             * @default
             * ```json
             * "auto"
             * ```
             */
            "icon-rotation-alignment"?: DataDrivenPropertyValueSpecification<"map" | "viewport" | "auto">,
            /**
             * Scales the original size of the icon by the provided factor. The new pixel size of the image will be the original pixel size multiplied by `icon-size`. 1 is the original size; 3 triples the size of the image.
             * 
             * @default
             * ```json
             * 1
             * ```
             */
            "icon-size"?: DataDrivenPropertyValueSpecification<number>,
            /**
             * Scales the icon to fit around the associated text.
             * 
             * @default
             * ```json
             * "none"
             * ```
             */
            "icon-text-fit"?: PropertyValueSpecification<"none" | "width" | "height" | "both">,
            /**
             * Size of the additional area added to dimensions determined by `icon-text-fit`, in clockwise order: top, right, bottom, left.
             * 
             * @default
             * ```json
             * [0, 0, 0, 0]
             * ```
             */
            "icon-text-fit-padding"?: PropertyValueSpecification<[number, number, number, number]>,
            /**
             * Name of image in sprite to use for drawing an image background.
             */
            "icon-image"?: DataDrivenPropertyValueSpecification<ResolvedImageSpecification>,
            /**
             * Rotates the icon clockwise.
             */
            "icon-rotate"?: DataDrivenPropertyValueSpecification<number>,
            /**
             * Size of additional area round the icon bounding box used for detecting symbol collisions.
             * 
             * @default
             * ```json
             * [2]
             * ```
             */
            "icon-padding"?: DataDrivenPropertyValueSpecification<PaddingSpecification>,
            /**
             * If true, the icon may be flipped to prevent it from being rendered upside-down.
             */
            "icon-keep-upright"?: PropertyValueSpecification<boolean>,
            /**
             * Offset distance of icon from its anchor. Positive values indicate right and down, while negative values indicate left and up. Each component is multiplied by the value of `icon-size` to obtain the final offset in pixels. When combined with `icon-rotate` the offset will be as if the rotated direction was up.
             * 
             * @default
             * ```json
             * [0, 0]
             * ```
             */
            "icon-offset"?: DataDrivenPropertyValueSpecification<[number, number]>,
            /**
             * Part of the icon placed closest to the anchor.
             * 
             * @default
             * ```json
             * "center"
             * ```
             */
            "icon-anchor"?: DataDrivenPropertyValueSpecification<"center" | "left" | "right" | "top" | "bottom" | "top-left" | "top-right" | "bottom-left" | "bottom-right">,
            /**
             * Orientation of icon when map is pitched.
             * 
             * @default
             * ```json
             * "auto"
             * ```
             */
            "icon-pitch-alignment"?: PropertyValueSpecification<"map" | "viewport" | "auto">,
            /**
             * Orientation of text when map is pitched.
             * 
             * @default
             * ```json
             * "auto"
             * ```
             */
            "text-pitch-alignment"?: PropertyValueSpecification<"map" | "viewport" | "auto">,
            /**
             * In combination with `symbol-placement`, determines the rotation behavior of the individual glyphs forming the text.
             * 
             * @default
             * ```json
             * "auto"
             * ```
             */
            "text-rotation-alignment"?: PropertyValueSpecification<"map" | "viewport" | "viewport-glyph" | "auto">,
            /**
             * Value to use for a text label. If a plain `string` is provided, it will be treated as a `formatted` with default/inherited formatting options.
             */
            "text-field"?: DataDrivenPropertyValueSpecification<FormattedSpecification>,
            /**
             * Fonts to use for displaying text. If the `glyphs` root property is specified, this array is joined together and interpreted as a font stack name. Otherwise, it is interpreted as a cascading fallback list of local font names.
             * 
             * @default
             * ```json
             * ["Open Sans Regular", "Arial Unicode MS Regular"]
             * ```
             */
            "text-font"?: DataDrivenPropertyValueSpecification<Array<string>>,
            /**
             * Font size.
             * 
             * @default
             * ```json
             * 16
             * ```
             */
            "text-size"?: DataDrivenPropertyValueSpecification<number>,
            /**
             * The maximum line width for text wrapping.
             * 
             * @default
             * ```json
             * 10
             * ```
             */
            "text-max-width"?: DataDrivenPropertyValueSpecification<number>,
            /**
             * Text leading value for multi-line text.
             * 
             * @default
             * ```json
             * 1.2
             * ```
             */
            "text-line-height"?: PropertyValueSpecification<number>,
            /**
             * Text tracking amount.
             */
            "text-letter-spacing"?: DataDrivenPropertyValueSpecification<number>,
            /**
             * Text justification options.
             * 
             * @default
             * ```json
             * "center"
             * ```
             */
            "text-justify"?: DataDrivenPropertyValueSpecification<"auto" | "left" | "center" | "right">,
            /**
             * Radial offset of text, in the direction of the symbol's anchor. Useful in combination with `text-variable-anchor`, which defaults to using the two-dimensional `text-offset` if present.
             */
            "text-radial-offset"?: DataDrivenPropertyValueSpecification<number>,
            /**
             * To increase the chance of placing high-priority labels on the map, you can provide an array of `text-anchor` locations: the renderer will attempt to place the label at each location, in order, before moving onto the next label. Use `text-justify: auto` to choose justification based on anchor position. To apply an offset, use the `text-radial-offset` or the two-dimensional `text-offset`.
             * 
             * @example
             * ```json
             * ["center", "left", "right"]
             * ```
             */
            "text-variable-anchor"?: PropertyValueSpecification<Array<"center" | "left" | "right" | "top" | "bottom" | "top-left" | "top-right" | "bottom-left" | "bottom-right">>,
            /**
             * To increase the chance of placing high-priority labels on the map, you can provide an array of `text-anchor` locations, each paired with an offset value. The renderer will attempt to place the label at each location, in order, before moving on to the next location+offset. Use `text-justify: auto` to choose justification based on anchor position. 
             * 
             *  The length of the array must be even, and must alternate between enum and point entries. i.e., each anchor location must be accompanied by a point, and that point defines the offset when the corresponding anchor location is used. Positive offset values indicate right and down, while negative values indicate left and up. Anchor locations may repeat, allowing the renderer to try multiple offsets to try and place a label using the same anchor. 
             * 
             *  When present, this property takes precedence over `text-anchor`, `text-variable-anchor`, `text-offset`, and `text-radial-offset`. 
             * 
             *  ```json 
             * 
             *  { "text-variable-anchor-offset": ["top", [0, 4], "left", [3,0], "bottom", [1, 1]] } 
             * 
             *  ``` 
             * 
             *  When the renderer chooses the `top` anchor, `[0, 4]` will be used for `text-offset`; the text will be shifted down by 4 ems. 
             * 
             *  When the renderer chooses the `left` anchor, `[3, 0]` will be used for `text-offset`; the text will be shifted right by 3 ems.
             * 
             * @example
             * ```json
             * ["top", [0, 4], "left", [3, 0], "bottom", [1, 1]]
             * ```
             */
            "text-variable-anchor-offset"?: DataDrivenPropertyValueSpecification<VariableAnchorOffsetCollectionSpecification>,
            /**
             * Part of the text placed closest to the anchor.
             * 
             * @default
             * ```json
             * "center"
             * ```
             */
            "text-anchor"?: DataDrivenPropertyValueSpecification<"center" | "left" | "right" | "top" | "bottom" | "top-left" | "top-right" | "bottom-left" | "bottom-right">,
            /**
             * Maximum angle change between adjacent characters.
             * 
             * @default
             * ```json
             * 45
             * ```
             */
            "text-max-angle"?: PropertyValueSpecification<number>,
            /**
             * The property allows control over a symbol's orientation. Note that the property values act as a hint, so that a symbol whose language doesn’t support the provided orientation will be laid out in its natural orientation. Example: English point symbol will be rendered horizontally even if array value contains single 'vertical' enum value. The order of elements in an array define priority order for the placement of an orientation variant.
             */
            "text-writing-mode"?: PropertyValueSpecification<Array<"horizontal" | "vertical">>,
            /**
             * Rotates the text clockwise.
             */
            "text-rotate"?: DataDrivenPropertyValueSpecification<number>,
            /**
             * Size of the additional area around the text bounding box used for detecting symbol collisions.
             * 
             * @default
             * ```json
             * 2
             * ```
             */
            "text-padding"?: PropertyValueSpecification<number>,
            /**
             * If true, the text may be flipped vertically to prevent it from being rendered upside-down.
             * 
             * @default
             * ```json
             * true
             * ```
             */
            "text-keep-upright"?: PropertyValueSpecification<boolean>,
            /**
             * Specifies how to capitalize text, similar to the CSS `text-transform` property.
             * 
             * @default
             * ```json
             * "none"
             * ```
             */
            "text-transform"?: DataDrivenPropertyValueSpecification<"none" | "uppercase" | "lowercase">,
            /**
             * Offset distance of text from its anchor. Positive values indicate right and down, while negative values indicate left and up. If used with text-variable-anchor, input values will be taken as absolute values. Offsets along the x- and y-axis will be applied automatically based on the anchor position.
             * 
             * @default
             * ```json
             * [0, 0]
             * ```
             */
            "text-offset"?: DataDrivenPropertyValueSpecification<[number, number]>,
            /**
             * If true, the text will be visible even if it collides with other previously drawn symbols.
             */
            "text-allow-overlap"?: PropertyValueSpecification<boolean>,
            /**
             * Allows for control over whether to show symbol text when it overlaps other symbols on the map. If `text-overlap` is not set, `text-allow-overlap` is used instead
             */
            "text-overlap"?: PropertyValueSpecification<"never" | "always" | "cooperative">,
            /**
             * If true, other symbols can be visible even if they collide with the text.
             */
            "text-ignore-placement"?: PropertyValueSpecification<boolean>,
            /**
             * If true, icons will display without their corresponding text when the text collides with other symbols and the icon does not.
             */
            "text-optional"?: PropertyValueSpecification<boolean>,
            /**
             * The height above the anchor, in meters, at which the symbol is placed. Use `symbol-height-anchor` to control what this height is measured from.
             */
            "symbol-height-offset"?: DataDrivenPropertyValueSpecification<number>,
            /**
             * Defines what `symbol-height-offset` is measured from.
             * 
             * @default
             * ```json
             * "ground"
             * ```
             */
            "symbol-height-anchor"?: PropertyValueSpecification<"ground" | "absolute">,
            /**
             * Whether this layer is displayed.
             * 
             * @default
             * ```json
             * "visible"
             * ```
             */
            "visibility"?: VisibilitySpecification
        },
    /**
     * Default paint properties for this layer.
     */
    "paint"?: {
            /**
             * The opacity at which the icon will be drawn.
             * 
             * @default
             * ```json
             * 1
             * ```
             */
            "icon-opacity"?: DataDrivenPropertyValueSpecification<number>,
            "icon-opacity-transition"?: TransitionSpecification,
            /**
             * The color of the icon. This can only be used with SDF icons.
             * 
             * @default
             * ```json
             * "#000000"
             * ```
             */
            "icon-color"?: DataDrivenPropertyValueSpecification<ColorSpecification>,
            "icon-color-transition"?: TransitionSpecification,
            /**
             * The color of the icon's halo. Icon halos can only be used with SDF icons.
             * 
             * @default
             * ```json
             * "rgba(0, 0, 0, 0)"
             * ```
             */
            "icon-halo-color"?: DataDrivenPropertyValueSpecification<ColorSpecification>,
            "icon-halo-color-transition"?: TransitionSpecification,
            /**
             * Distance of halo to the icon outline. 
             * 
             * The unit is in pixels only for SDF sprites that were created with a blur radius of 8, multiplied by the display density. I.e., the radius needs to be 16 for `@2x` sprites, etc.
             */
            "icon-halo-width"?: DataDrivenPropertyValueSpecification<number>,
            "icon-halo-width-transition"?: TransitionSpecification,
            /**
             * Fade out the halo towards the outside.
             */
            "icon-halo-blur"?: DataDrivenPropertyValueSpecification<number>,
            "icon-halo-blur-transition"?: TransitionSpecification,
            /**
             * Distance that the icon's anchor is moved from its original placement. Positive values indicate right and down, while negative values indicate left and up.
             * 
             * @default
             * ```json
             * [0, 0]
             * ```
             */
            "icon-translate"?: PropertyValueSpecification<[number, number]>,
            "icon-translate-transition"?: TransitionSpecification,
            /**
             * Controls the frame of reference for `icon-translate`.
             * 
             * @default
             * ```json
             * "map"
             * ```
             */
            "icon-translate-anchor"?: PropertyValueSpecification<"map" | "viewport">,
            /**
             * The opacity at which the text will be drawn.
             * 
             * @default
             * ```json
             * 1
             * ```
             */
            "text-opacity"?: DataDrivenPropertyValueSpecification<number>,
            "text-opacity-transition"?: TransitionSpecification,
            /**
             * The color with which the text will be drawn.
             * 
             * @default
             * ```json
             * "#000000"
             * ```
             */
            "text-color"?: DataDrivenPropertyValueSpecification<ColorSpecification>,
            "text-color-transition"?: TransitionSpecification,
            /**
             * The color of the text's halo, which helps it stand out from backgrounds.
             * 
             * @default
             * ```json
             * "rgba(0, 0, 0, 0)"
             * ```
             */
            "text-halo-color"?: DataDrivenPropertyValueSpecification<ColorSpecification>,
            "text-halo-color-transition"?: TransitionSpecification,
            /**
             * Distance of halo to the font outline. Max text halo width is 1/4 of the font-size.
             */
            "text-halo-width"?: DataDrivenPropertyValueSpecification<number>,
            "text-halo-width-transition"?: TransitionSpecification,
            /**
             * The halo's fadeout distance towards the outside.
             */
            "text-halo-blur"?: DataDrivenPropertyValueSpecification<number>,
            "text-halo-blur-transition"?: TransitionSpecification,
            /**
             * Distance that the text's anchor is moved from its original placement. Positive values indicate right and down, while negative values indicate left and up.
             * 
             * @default
             * ```json
             * [0, 0]
             * ```
             */
            "text-translate"?: PropertyValueSpecification<[number, number]>,
            "text-translate-transition"?: TransitionSpecification,
            /**
             * Controls the frame of reference for `text-translate`.
             * 
             * @default
             * ```json
             * "map"
             * ```
             */
            "text-translate-anchor"?: PropertyValueSpecification<"map" | "viewport">
        }
};

export type CircleLayerSpecification = {
    /**
     * Unique layer name.
     */
    "id": string,
    "type": "circle",
    /**
     * Arbitrary properties useful to track with the layer, but do not influence rendering. Properties should be prefixed to avoid collisions, like 'maplibre:'.
     * 
     * @example
     * ```json
     * {"source:comment": "Hydrology FCCODE 460 - Narrow wash"}
     * ```
     */
    "metadata"?: unknown,
    /**
     * Name of a source description to be used for this layer. Required for all layer types except `background`.
     */
    "source": string,
    /**
     * Layer to use from a vector tile source. Required for vector tile sources; prohibited for all other source types, including GeoJSON sources.
     */
    "source-layer"?: string,
    /**
     * The minimum zoom level for the layer. At zoom levels less than the minzoom, the layer will be hidden.
     */
    "minzoom"?: number,
    /**
     * The maximum zoom level for the layer. At zoom levels equal to or greater than the maxzoom, the layer will be hidden.
     */
    "maxzoom"?: number,
    /**
     * A expression specifying conditions on source features. Only features that match the filter are displayed. Zoom expressions in filters are only evaluated at integer zoom levels. The `feature-state` expression is not supported in filter expressions.
     */
    "filter"?: FilterSpecification,
    /**
     * Layout properties for the layer.
     */
    "layout"?: {
            /**
             * Sorts features in ascending order based on this value. Features with a higher sort key will appear above features with a lower sort key.
             */
            "circle-sort-key"?: DataDrivenPropertyValueSpecification<number>,
            /**
             * Whether this layer is displayed.
             * 
             * @default
             * ```json
             * "visible"
             * ```
             */
            "visibility"?: VisibilitySpecification
        },
    /**
     * Default paint properties for this layer.
     */
    "paint"?: {
            /**
             * Circle radius.
             * 
             * @default
             * ```json
             * 5
             * ```
             */
            "circle-radius"?: DataDrivenPropertyValueSpecification<number>,
            "circle-radius-transition"?: TransitionSpecification,
            /**
             * The fill color of the circle.
             * 
             * @default
             * ```json
             * "#000000"
             * ```
             */
            "circle-color"?: DataDrivenPropertyValueSpecification<ColorSpecification>,
            "circle-color-transition"?: TransitionSpecification,
            /**
             * Amount to blur the circle. 1 blurs the circle such that only the centerpoint is full opacity.
             */
            "circle-blur"?: DataDrivenPropertyValueSpecification<number>,
            "circle-blur-transition"?: TransitionSpecification,
            /**
             * The opacity at which the circle will be drawn.
             * 
             * @default
             * ```json
             * 1
             * ```
             */
            "circle-opacity"?: DataDrivenPropertyValueSpecification<number>,
            "circle-opacity-transition"?: TransitionSpecification,
            /**
             * The geometry's offset. Values are `[x, y]` where negatives indicate left and up, respectively.
             * 
             * @default
             * ```json
             * [0, 0]
             * ```
             */
            "circle-translate"?: PropertyValueSpecification<[number, number]>,
            "circle-translate-transition"?: TransitionSpecification,
            /**
             * Controls the frame of reference for `circle-translate`.
             * 
             * @default
             * ```json
             * "map"
             * ```
             */
            "circle-translate-anchor"?: PropertyValueSpecification<"map" | "viewport">,
            /**
             * Controls the scaling behavior of the circle when the map is pitched.
             * 
             * @default
             * ```json
             * "map"
             * ```
             */
            "circle-pitch-scale"?: PropertyValueSpecification<"map" | "viewport">,
            /**
             * Orientation of circle when map is pitched.
             * 
             * @default
             * ```json
             * "viewport"
             * ```
             */
            "circle-pitch-alignment"?: PropertyValueSpecification<"map" | "viewport">,
            /**
             * The width of the circle's stroke. Strokes are placed outside of the `circle-radius`.
             */
            "circle-stroke-width"?: DataDrivenPropertyValueSpecification<number>,
            "circle-stroke-width-transition"?: TransitionSpecification,
            /**
             * The stroke color of the circle.
             * 
             * @default
             * ```json
             * "#000000"
             * ```
             */
            "circle-stroke-color"?: DataDrivenPropertyValueSpecification<ColorSpecification>,
            "circle-stroke-color-transition"?: TransitionSpecification,
            /**
             * The opacity of the circle's stroke.
             * 
             * @default
             * ```json
             * 1
             * ```
             */
            "circle-stroke-opacity"?: DataDrivenPropertyValueSpecification<number>,
            "circle-stroke-opacity-transition"?: TransitionSpecification
        }
};

export type HeatmapLayerSpecification = {
    /**
     * Unique layer name.
     */
    "id": string,
    "type": "heatmap",
    /**
     * Arbitrary properties useful to track with the layer, but do not influence rendering. Properties should be prefixed to avoid collisions, like 'maplibre:'.
     * 
     * @example
     * ```json
     * {"source:comment": "Hydrology FCCODE 460 - Narrow wash"}
     * ```
     */
    "metadata"?: unknown,
    /**
     * Name of a source description to be used for this layer. Required for all layer types except `background`.
     */
    "source": string,
    /**
     * Layer to use from a vector tile source. Required for vector tile sources; prohibited for all other source types, including GeoJSON sources.
     */
    "source-layer"?: string,
    /**
     * The minimum zoom level for the layer. At zoom levels less than the minzoom, the layer will be hidden.
     */
    "minzoom"?: number,
    /**
     * The maximum zoom level for the layer. At zoom levels equal to or greater than the maxzoom, the layer will be hidden.
     */
    "maxzoom"?: number,
    /**
     * A expression specifying conditions on source features. Only features that match the filter are displayed. Zoom expressions in filters are only evaluated at integer zoom levels. The `feature-state` expression is not supported in filter expressions.
     */
    "filter"?: FilterSpecification,
    /**
     * Layout properties for the layer.
     */
    "layout"?: {
            /**
             * Whether this layer is displayed.
             * 
             * @default
             * ```json
             * "visible"
             * ```
             */
            "visibility"?: VisibilitySpecification
        },
    /**
     * Default paint properties for this layer.
     */
    "paint"?: {
            /**
             * Radius of influence of one heatmap point in pixels. Increasing the value makes the heatmap smoother, but less detailed.
             * 
             * @default
             * ```json
             * 30
             * ```
             */
            "heatmap-radius"?: DataDrivenPropertyValueSpecification<number>,
            "heatmap-radius-transition"?: TransitionSpecification,
            /**
             * A measure of how much an individual point contributes to the heatmap. A value of 10 would be equivalent to having 10 points of weight 1 in the same spot. Especially useful when combined with clustering.
             * 
             * @default
             * ```json
             * 1
             * ```
             */
            "heatmap-weight"?: DataDrivenPropertyValueSpecification<number>,
            /**
             * Similar to `heatmap-weight` but controls the intensity of the heatmap globally. Primarily used for adjusting the heatmap based on zoom level.
             * 
             * @default
             * ```json
             * 1
             * ```
             */
            "heatmap-intensity"?: PropertyValueSpecification<number>,
            "heatmap-intensity-transition"?: TransitionSpecification,
            /**
             * Defines the color of each pixel based on its density value in a heatmap.  Should be an expression that uses `["heatmap-density"]` as input.
             * 
             * @default
             * ```json
             * [
             *     "interpolate",
             *     ["linear"],
             *     ["heatmap-density"],
             *     0,
             *     "rgba(0, 0, 255, 0)",
             *     0.1,
             *     "royalblue",
             *     0.3,
             *     "cyan",
             *     0.5,
             *     "lime",
             *     0.7,
             *     "yellow",
             *     1,
             *     "red"
             * ]
             * ```
             */
            "heatmap-color"?: ExpressionSpecification,
            /**
             * The global opacity at which the heatmap layer will be drawn.
             * 
             * @default
             * ```json
             * 1
             * ```
             */
            "heatmap-opacity"?: PropertyValueSpecification<number>,
            "heatmap-opacity-transition"?: TransitionSpecification
        }
};

export type FillExtrusionLayerSpecification = {
    /**
     * Unique layer name.
     */
    "id": string,
    "type": "fill-extrusion",
    /**
     * Arbitrary properties useful to track with the layer, but do not influence rendering. Properties should be prefixed to avoid collisions, like 'maplibre:'.
     * 
     * @example
     * ```json
     * {"source:comment": "Hydrology FCCODE 460 - Narrow wash"}
     * ```
     */
    "metadata"?: unknown,
    /**
     * Name of a source description to be used for this layer. Required for all layer types except `background`.
     */
    "source": string,
    /**
     * Layer to use from a vector tile source. Required for vector tile sources; prohibited for all other source types, including GeoJSON sources.
     */
    "source-layer"?: string,
    /**
     * The minimum zoom level for the layer. At zoom levels less than the minzoom, the layer will be hidden.
     */
    "minzoom"?: number,
    /**
     * The maximum zoom level for the layer. At zoom levels equal to or greater than the maxzoom, the layer will be hidden.
     */
    "maxzoom"?: number,
    /**
     * A expression specifying conditions on source features. Only features that match the filter are displayed. Zoom expressions in filters are only evaluated at integer zoom levels. The `feature-state` expression is not supported in filter expressions.
     */
    "filter"?: FilterSpecification,
    /**
     * Layout properties for the layer.
     */
    "layout"?: {
            /**
             * Whether this layer is displayed.
             * 
             * @default
             * ```json
             * "visible"
             * ```
             */
            "visibility"?: VisibilitySpecification,
            /**
             * The distance from each fill extrusion corner, measured along the adjacent edges, that is replaced by a rounded corner. A value of `0` disables rounded corners.
             */
            "fill-extrusion-rounded-corner-distance"?: number
        },
    /**
     * Default paint properties for this layer.
     */
    "paint"?: {
            /**
             * The opacity of the entire fill extrusion layer. This is rendered on a per-layer, not per-feature, basis, and data-driven styling is not available.
             * 
             * @default
             * ```json
             * 1
             * ```
             */
            "fill-extrusion-opacity"?: PropertyValueSpecification<number>,
            "fill-extrusion-opacity-transition"?: TransitionSpecification,
            /**
             * The base color of the extruded fill. The extrusion's surfaces will be shaded differently based on this color in combination with the root `light` settings. If this color is specified as `rgba` with an alpha component, the alpha component will be ignored; use `fill-extrusion-opacity` to set layer opacity.
             * 
             * @default
             * ```json
             * "#000000"
             * ```
             */
            "fill-extrusion-color"?: DataDrivenPropertyValueSpecification<ColorSpecification>,
            "fill-extrusion-color-transition"?: TransitionSpecification,
            /**
             * The geometry's offset. Values are `[x, y]` where negatives indicate left and up (on the flat plane), respectively.
             * 
             * @default
             * ```json
             * [0, 0]
             * ```
             */
            "fill-extrusion-translate"?: PropertyValueSpecification<[number, number]>,
            "fill-extrusion-translate-transition"?: TransitionSpecification,
            /**
             * Controls the frame of reference for `fill-extrusion-translate`.
             * 
             * @default
             * ```json
             * "map"
             * ```
             */
            "fill-extrusion-translate-anchor"?: PropertyValueSpecification<"map" | "viewport">,
            /**
             * Name of image in sprite to use for drawing images on extruded fills. For seamless patterns, image width and height must be a factor of two (2, 4, 8, ..., 512). Note that zoom-dependent expressions will be evaluated only at integer zoom levels.
             */
            "fill-extrusion-pattern"?: DataDrivenPropertyValueSpecification<ResolvedImageSpecification>,
            "fill-extrusion-pattern-transition"?: TransitionSpecification,
            /**
             * The height with which to extrude this layer. Negative values extrude below ground level, so a floor that is entirely underground can be expressed.
             */
            "fill-extrusion-height"?: DataDrivenPropertyValueSpecification<number>,
            "fill-extrusion-height-transition"?: TransitionSpecification,
            /**
             * The height with which to extrude the base of this layer. Must be less than or equal to `fill-extrusion-height`. Negative values extrude below ground level, e.g. underground floors.
             */
            "fill-extrusion-base"?: DataDrivenPropertyValueSpecification<number>,
            "fill-extrusion-base-transition"?: TransitionSpecification,
            /**
             * Whether to apply a vertical gradient to the sides of a fill-extrusion layer. If true, sides will be shaded slightly darker farther down.
             * 
             * @default
             * ```json
             * true
             * ```
             */
            "fill-extrusion-vertical-gradient"?: PropertyValueSpecification<boolean>
        }
};

export type RasterLayerSpecification = {
    /**
     * Unique layer name.
     */
    "id": string,
    "type": "raster",
    /**
     * Arbitrary properties useful to track with the layer, but do not influence rendering. Properties should be prefixed to avoid collisions, like 'maplibre:'.
     * 
     * @example
     * ```json
     * {"source:comment": "Hydrology FCCODE 460 - Narrow wash"}
     * ```
     */
    "metadata"?: unknown,
    /**
     * Name of a source description to be used for this layer. Required for all layer types except `background`.
     */
    "source": string,
    /**
     * Layer to use from a vector tile source. Required for vector tile sources; prohibited for all other source types, including GeoJSON sources.
     */
    "source-layer"?: string,
    /**
     * The minimum zoom level for the layer. At zoom levels less than the minzoom, the layer will be hidden.
     */
    "minzoom"?: number,
    /**
     * The maximum zoom level for the layer. At zoom levels equal to or greater than the maxzoom, the layer will be hidden.
     */
    "maxzoom"?: number,
    /**
     * A expression specifying conditions on source features. Only features that match the filter are displayed. Zoom expressions in filters are only evaluated at integer zoom levels. The `feature-state` expression is not supported in filter expressions.
     */
    "filter"?: FilterSpecification,
    /**
     * Layout properties for the layer.
     */
    "layout"?: {
            /**
             * Whether this layer is displayed.
             * 
             * @default
             * ```json
             * "visible"
             * ```
             */
            "visibility"?: VisibilitySpecification
        },
    /**
     * Default paint properties for this layer.
     */
    "paint"?: {
            /**
             * The opacity at which the image will be drawn.
             * 
             * @default
             * ```json
             * 1
             * ```
             */
            "raster-opacity"?: PropertyValueSpecification<number>,
            "raster-opacity-transition"?: TransitionSpecification,
            /**
             * Rotates hues around the color wheel.
             */
            "raster-hue-rotate"?: PropertyValueSpecification<number>,
            "raster-hue-rotate-transition"?: TransitionSpecification,
            /**
             * Increase or reduce the brightness of the image. The value is the minimum brightness.
             */
            "raster-brightness-min"?: PropertyValueSpecification<number>,
            "raster-brightness-min-transition"?: TransitionSpecification,
            /**
             * Increase or reduce the brightness of the image. The value is the maximum brightness.
             * 
             * @default
             * ```json
             * 1
             * ```
             */
            "raster-brightness-max"?: PropertyValueSpecification<number>,
            "raster-brightness-max-transition"?: TransitionSpecification,
            /**
             * Increase or reduce the saturation of the image.
             */
            "raster-saturation"?: PropertyValueSpecification<number>,
            "raster-saturation-transition"?: TransitionSpecification,
            /**
             * Increase or reduce the contrast of the image.
             */
            "raster-contrast"?: PropertyValueSpecification<number>,
            "raster-contrast-transition"?: TransitionSpecification,
            /**
             * The resampling/interpolation method to use for overscaling, also known as texture magnification filter.
             * ![Visual comparison of linear resampling versus nearest resampling](assets/resampling.png)
             * 
             * @default
             * ```json
             * "linear"
             * ```
             */
            "resampling"?: PropertyValueSpecification<"linear" | "nearest">,
            /**
             * The resampling/interpolation method to use for overscaling, also known as texture magnification filter. It is advised to use the generic `resampling` paint property instead.
             * 
             * @default
             * ```json
             * "linear"
             * ```
             */
            "raster-resampling"?: PropertyValueSpecification<"linear" | "nearest">,
            /**
             * Fade duration when a new tile is added, or when a video is started or its coordinates are updated.
             * 
             * @default
             * ```json
             * 300
             * ```
             */
            "raster-fade-duration"?: PropertyValueSpecification<number>
        }
};

export type HillshadeLayerSpecification = {
    /**
     * Unique layer name.
     */
    "id": string,
    "type": "hillshade",
    /**
     * Arbitrary properties useful to track with the layer, but do not influence rendering. Properties should be prefixed to avoid collisions, like 'maplibre:'.
     * 
     * @example
     * ```json
     * {"source:comment": "Hydrology FCCODE 460 - Narrow wash"}
     * ```
     */
    "metadata"?: unknown,
    /**
     * Name of a source description to be used for this layer. Required for all layer types except `background`.
     */
    "source": string,
    /**
     * Layer to use from a vector tile source. Required for vector tile sources; prohibited for all other source types, including GeoJSON sources.
     */
    "source-layer"?: string,
    /**
     * The minimum zoom level for the layer. At zoom levels less than the minzoom, the layer will be hidden.
     */
    "minzoom"?: number,
    /**
     * The maximum zoom level for the layer. At zoom levels equal to or greater than the maxzoom, the layer will be hidden.
     */
    "maxzoom"?: number,
    /**
     * A expression specifying conditions on source features. Only features that match the filter are displayed. Zoom expressions in filters are only evaluated at integer zoom levels. The `feature-state` expression is not supported in filter expressions.
     */
    "filter"?: FilterSpecification,
    /**
     * Layout properties for the layer.
     */
    "layout"?: {
            /**
             * Whether this layer is displayed.
             * 
             * @default
             * ```json
             * "visible"
             * ```
             */
            "visibility"?: VisibilitySpecification
        },
    /**
     * Default paint properties for this layer.
     */
    "paint"?: {
            /**
             * The direction of the light source(s) used to generate the hillshading with 0 as the top of the viewport if `hillshade-illumination-anchor` is set to `viewport` and due north if `hillshade-illumination-anchor` is set to `map`. Only when `hillshade-method` is set to `multidirectional` can you specify multiple light sources.
             * 
             * @default
             * ```json
             * 335
             * ```
             */
            "hillshade-illumination-direction"?: PropertyValueSpecification<NumberArraySpecification>,
            /**
             * The altitude of the light source(s) used to generate the hillshading with 0 as sunset and 90 as noon. Only when `hillshade-method` is set to `multidirectional` can you specify multiple light sources.
             * 
             * @default
             * ```json
             * 45
             * ```
             */
            "hillshade-illumination-altitude"?: PropertyValueSpecification<NumberArraySpecification>,
            /**
             * Direction of light source when map is rotated.
             * 
             * @default
             * ```json
             * "viewport"
             * ```
             */
            "hillshade-illumination-anchor"?: PropertyValueSpecification<"map" | "viewport">,
            /**
             * Intensity of the hillshade
             * 
             * @default
             * ```json
             * 0.5
             * ```
             */
            "hillshade-exaggeration"?: PropertyValueSpecification<number>,
            "hillshade-exaggeration-transition"?: TransitionSpecification,
            /**
             * The shading color of areas that face away from the light source(s). Only when `hillshade-method` is set to `multidirectional` can you specify multiple light sources.
             * 
             * @default
             * ```json
             * "#000000"
             * ```
             */
            "hillshade-shadow-color"?: PropertyValueSpecification<ColorArraySpecification>,
            "hillshade-shadow-color-transition"?: TransitionSpecification,
            /**
             * The shading color of areas that faces towards the light source(s). Only when `hillshade-method` is set to `multidirectional` can you specify multiple light sources.
             * 
             * @default
             * ```json
             * "#FFFFFF"
             * ```
             */
            "hillshade-highlight-color"?: PropertyValueSpecification<ColorArraySpecification>,
            "hillshade-highlight-color-transition"?: TransitionSpecification,
            /**
             * The shading color used to accentuate rugged terrain like sharp cliffs and gorges.
             * 
             * @default
             * ```json
             * "#000000"
             * ```
             */
            "hillshade-accent-color"?: PropertyValueSpecification<ColorSpecification>,
            "hillshade-accent-color-transition"?: TransitionSpecification,
            /**
             * The hillshade algorithm to use, one of `standard`, `basic`, `combined`, `igor`, or `multidirectional`.
             * ![Visual comparison of standard, basic, igor, combined, and multidirectional hillshade-method](assets/hillshade_methods.png)
             * 
             * @default
             * ```json
             * "standard"
             * ```
             */
            "hillshade-method"?: PropertyValueSpecification<"standard" | "basic" | "combined" | "igor" | "multidirectional">,
            /**
             * The resampling/interpolation method to use for overscaling, also known as texture magnification filter.
             * ![Visual comparison of linear resampling versus nearest resampling](assets/resampling.png)
             * 
             * @default
             * ```json
             * "linear"
             * ```
             */
            "resampling"?: PropertyValueSpecification<"linear" | "nearest">
        }
};

export type ColorReliefLayerSpecification = {
    /**
     * Unique layer name.
     */
    "id": string,
    "type": "color-relief",
    /**
     * Arbitrary properties useful to track with the layer, but do not influence rendering. Properties should be prefixed to avoid collisions, like 'maplibre:'.
     * 
     * @example
     * ```json
     * {"source:comment": "Hydrology FCCODE 460 - Narrow wash"}
     * ```
     */
    "metadata"?: unknown,
    /**
     * Name of a source description to be used for this layer. Required for all layer types except `background`.
     */
    "source": string,
    /**
     * Layer to use from a vector tile source. Required for vector tile sources; prohibited for all other source types, including GeoJSON sources.
     */
    "source-layer"?: string,
    /**
     * The minimum zoom level for the layer. At zoom levels less than the minzoom, the layer will be hidden.
     */
    "minzoom"?: number,
    /**
     * The maximum zoom level for the layer. At zoom levels equal to or greater than the maxzoom, the layer will be hidden.
     */
    "maxzoom"?: number,
    /**
     * A expression specifying conditions on source features. Only features that match the filter are displayed. Zoom expressions in filters are only evaluated at integer zoom levels. The `feature-state` expression is not supported in filter expressions.
     */
    "filter"?: FilterSpecification,
    /**
     * Layout properties for the layer.
     */
    "layout"?: {
            /**
             * Whether this layer is displayed.
             * 
             * @default
             * ```json
             * "visible"
             * ```
             */
            "visibility"?: VisibilitySpecification
        },
    /**
     * Default paint properties for this layer.
     */
    "paint"?: {
            /**
             * The opacity at which the color-relief will be drawn.
             * 
             * @default
             * ```json
             * 1
             * ```
             */
            "color-relief-opacity"?: PropertyValueSpecification<number>,
            "color-relief-opacity-transition"?: TransitionSpecification,
            /**
             * Defines the color of each pixel based on its elevation. Should be an expression that uses `["elevation"]` as input.
             * 
             * @example
             * ```json
             * [
             *     "interpolate",
             *     ["linear"],
             *     ["elevation"],
             *     0,
             *     "black",
             *     8849,
             *     "white"
             * ]
             * ```
             */
            "color-relief-color"?: ExpressionSpecification,
            /**
             * The resampling/interpolation method to use for overscaling, also known as texture magnification filter.
             * ![Visual comparison of linear resampling versus nearest resampling](assets/resampling.png)
             * 
             * @default
             * ```json
             * "linear"
             * ```
             */
            "resampling"?: PropertyValueSpecification<"linear" | "nearest">
        }
};

export type BackgroundLayerSpecification = {
    /**
     * Unique layer name.
     */
    "id": string,
    "type": "background",
    /**
     * Arbitrary properties useful to track with the layer, but do not influence rendering. Properties should be prefixed to avoid collisions, like 'maplibre:'.
     * 
     * @example
     * ```json
     * {"source:comment": "Hydrology FCCODE 460 - Narrow wash"}
     * ```
     */
    "metadata"?: unknown,
    /**
     * The minimum zoom level for the layer. At zoom levels less than the minzoom, the layer will be hidden.
     */
    "minzoom"?: number,
    /**
     * The maximum zoom level for the layer. At zoom levels equal to or greater than the maxzoom, the layer will be hidden.
     */
    "maxzoom"?: number,
    /**
     * Layout properties for the layer.
     */
    "layout"?: {
            /**
             * Whether this layer is displayed.
             * 
             * @default
             * ```json
             * "visible"
             * ```
             */
            "visibility"?: VisibilitySpecification
        },
    /**
     * Default paint properties for this layer.
     */
    "paint"?: {
            /**
             * The color with which the background will be drawn.
             * 
             * @default
             * ```json
             * "#000000"
             * ```
             */
            "background-color"?: PropertyValueSpecification<ColorSpecification>,
            "background-color-transition"?: TransitionSpecification,
            /**
             * Name of image in sprite to use for drawing an image background. For seamless patterns, image width and height must be a factor of two (2, 4, 8, ..., 512). Note that zoom-dependent expressions will be evaluated only at integer zoom levels.
             */
            "background-pattern"?: PropertyValueSpecification<ResolvedImageSpecification>,
            "background-pattern-transition"?: TransitionSpecification,
            /**
             * The opacity at which the background will be drawn.
             * 
             * @default
             * ```json
             * 1
             * ```
             */
            "background-opacity"?: PropertyValueSpecification<number>,
            "background-opacity-transition"?: TransitionSpecification
        }
};

export type LayerSpecification =
    | FillLayerSpecification
    | LineLayerSpecification
    | SymbolLayerSpecification
    | CircleLayerSpecification
    | HeatmapLayerSpecification
    | FillExtrusionLayerSpecification
    | RasterLayerSpecification
    | HillshadeLayerSpecification
    | ColorReliefLayerSpecification
    | BackgroundLayerSpecification;

/**
 * Union of all paint properties across all layer types.
 */
export type AllPaintProperties = {
    /**
     * Whether or not the fill should be antialiased.
     * 
     * @default
     * ```json
     * true
     * ```
     */
    "fill-antialias"?: PropertyValueSpecification<boolean>,
    /**
     * The opacity of the entire fill layer. In contrast to the `fill-color`, this value will also affect the 1px stroke around the fill, if the stroke is used.
     * 
     * @default
     * ```json
     * 1
     * ```
     */
    "fill-opacity"?: DataDrivenPropertyValueSpecification<number>,
    "fill-opacity-transition"?: TransitionSpecification,
    /**
     * Opacity applied to the layer as a whole. Unlike `fill-opacity` and alpha values in `fill-color`, which are applied per feature and accumulate where fills overlap, `fill-layer-opacity` is applied once so overlapping fills appear as a single surface at the given opacity. When both `fill-opacity` and `fill-layer-opacity` are set, the per-feature, overlap accumulation is preserved, then `fill-layer-opacity` composites the result. This property affects only the layer it is set on and cannot be used to composite multiple layers together or control how this layer blends with layers above or below it.
     * 
     * ![fill-opacity vs. fill-layer-opacity](assets/fill-layer-opacity.svg)
     * 
     * @default
     * ```json
     * 1
     * ```
     */
    "fill-layer-opacity"?: PropertyValueSpecification<number>,
    "fill-layer-opacity-transition"?: TransitionSpecification,
    /**
     * The color of the filled part of this layer. This color can be specified as `rgba` with an alpha component and the color's opacity will not affect the opacity of the 1px stroke, if it is used. When used with an SDF fill pattern, this serves as the foreground color of the pattern.
     * 
     * @default
     * ```json
     * "#000000"
     * ```
     */
    "fill-color"?: DataDrivenPropertyValueSpecification<ColorSpecification>,
    "fill-color-transition"?: TransitionSpecification,
    /**
     * The outline color of the fill. Matches the value of `fill-color` if unspecified.
     */
    "fill-outline-color"?: DataDrivenPropertyValueSpecification<ColorSpecification>,
    "fill-outline-color-transition"?: TransitionSpecification,
    /**
     * The geometry's offset. Values are `[x, y]` where negatives indicate left and up, respectively.
     * 
     * @default
     * ```json
     * [0, 0]
     * ```
     */
    "fill-translate"?: PropertyValueSpecification<[number, number]>,
    "fill-translate-transition"?: TransitionSpecification,
    /**
     * Controls the frame of reference for `fill-translate`.
     * 
     * @default
     * ```json
     * "map"
     * ```
     */
    "fill-translate-anchor"?: PropertyValueSpecification<"map" | "viewport">,
    /**
     * Name of image in sprite to use for drawing image fills. For seamless patterns, image width and height must be a factor of two (2, 4, 8, ..., 512). Note that zoom-dependent expressions will be evaluated only at integer zoom levels.
     */
    "fill-pattern"?: DataDrivenPropertyValueSpecification<ResolvedImageSpecification>,
    "fill-pattern-transition"?: TransitionSpecification,
    /**
     * The opacity at which the line will be drawn.
     * 
     * @default
     * ```json
     * 1
     * ```
     */
    "line-opacity"?: DataDrivenPropertyValueSpecification<number>,
    "line-opacity-transition"?: TransitionSpecification,
    /**
     * Opacity applied to the layer as a whole. Unlike `line-opacity` and alpha values in `line-color`, which are applied per feature and accumulate where lines overlap, `line-layer-opacity` is applied once so overlapping lines appear as a single surface at the given opacity. When both `line-opacity` and `line-layer-opacity` are set, the per-feature, overlap accumulation is preserved, then layer-opacity composites the result. This property affects only the layer it is set on and cannot be used to composite multiple layers together or control how this layer blends with layers above or below it.
     * 
     * ![line-opacity vs. line-layer-opacity](assets/line-layer-opacity.svg)
     * 
     * @default
     * ```json
     * 1
     * ```
     */
    "line-layer-opacity"?: PropertyValueSpecification<number>,
    "line-layer-opacity-transition"?: TransitionSpecification,
    /**
     * The color with which the line will be drawn.
     * 
     * @default
     * ```json
     * "#000000"
     * ```
     */
    "line-color"?: DataDrivenPropertyValueSpecification<ColorSpecification>,
    "line-color-transition"?: TransitionSpecification,
    /**
     * The geometry's offset. Values are `[x, y]` where negatives indicate left and up, respectively.
     * 
     * @default
     * ```json
     * [0, 0]
     * ```
     */
    "line-translate"?: PropertyValueSpecification<[number, number]>,
    "line-translate-transition"?: TransitionSpecification,
    /**
     * Controls the frame of reference for `line-translate`.
     * 
     * @default
     * ```json
     * "map"
     * ```
     */
    "line-translate-anchor"?: PropertyValueSpecification<"map" | "viewport">,
    /**
     * Stroke thickness.
     * 
     * @default
     * ```json
     * 1
     * ```
     */
    "line-width"?: DataDrivenPropertyValueSpecification<number>,
    "line-width-transition"?: TransitionSpecification,
    /**
     * Draws a line casing outside of a line's actual path. Value indicates the width of the inner gap.
     */
    "line-gap-width"?: DataDrivenPropertyValueSpecification<number>,
    "line-gap-width-transition"?: TransitionSpecification,
    /**
     * The line's offset. For linear features, a positive value offsets the line to the right, relative to the direction of the line, and a negative value to the left. For polygon features, a positive value results in an inset, and a negative value results in an outset.
     */
    "line-offset"?: DataDrivenPropertyValueSpecification<number>,
    "line-offset-transition"?: TransitionSpecification,
    /**
     * Blur applied to the line, in pixels.
     */
    "line-blur"?: DataDrivenPropertyValueSpecification<number>,
    "line-blur-transition"?: TransitionSpecification,
    /**
     * Specifies the lengths of the alternating dashes and gaps that form the dash pattern. The lengths are later scaled by the line width. To convert a dash length to pixels, multiply the length by the current line width. GeoJSON sources with `lineMetrics: true` specified won't render dashed lines to the expected scale. Zoom-dependent expressions will be evaluated only at integer zoom levels. The only way to create an array value is using `["literal", [...]]`; arrays cannot be read from or derived from feature properties.
     */
    "line-dasharray"?: DataDrivenPropertyValueSpecification<Array<number>>,
    "line-dasharray-transition"?: TransitionSpecification,
    /**
     * Name of image in sprite to use for drawing image lines. For seamless patterns, image width must be a factor of two (2, 4, 8, ..., 512). Note that zoom-dependent expressions will be evaluated only at integer zoom levels.
     */
    "line-pattern"?: DataDrivenPropertyValueSpecification<ResolvedImageSpecification>,
    "line-pattern-transition"?: TransitionSpecification,
    /**
     * Defines a gradient with which to color a line feature. Can only be used with GeoJSON sources that specify `"lineMetrics": true`.
     */
    "line-gradient"?: ExpressionSpecification,
    /**
     * The opacity at which the icon will be drawn.
     * 
     * @default
     * ```json
     * 1
     * ```
     */
    "icon-opacity"?: DataDrivenPropertyValueSpecification<number>,
    "icon-opacity-transition"?: TransitionSpecification,
    /**
     * The color of the icon. This can only be used with SDF icons.
     * 
     * @default
     * ```json
     * "#000000"
     * ```
     */
    "icon-color"?: DataDrivenPropertyValueSpecification<ColorSpecification>,
    "icon-color-transition"?: TransitionSpecification,
    /**
     * The color of the icon's halo. Icon halos can only be used with SDF icons.
     * 
     * @default
     * ```json
     * "rgba(0, 0, 0, 0)"
     * ```
     */
    "icon-halo-color"?: DataDrivenPropertyValueSpecification<ColorSpecification>,
    "icon-halo-color-transition"?: TransitionSpecification,
    /**
     * Distance of halo to the icon outline. 
     * 
     * The unit is in pixels only for SDF sprites that were created with a blur radius of 8, multiplied by the display density. I.e., the radius needs to be 16 for `@2x` sprites, etc.
     */
    "icon-halo-width"?: DataDrivenPropertyValueSpecification<number>,
    "icon-halo-width-transition"?: TransitionSpecification,
    /**
     * Fade out the halo towards the outside.
     */
    "icon-halo-blur"?: DataDrivenPropertyValueSpecification<number>,
    "icon-halo-blur-transition"?: TransitionSpecification,
    /**
     * Distance that the icon's anchor is moved from its original placement. Positive values indicate right and down, while negative values indicate left and up.
     * 
     * @default
     * ```json
     * [0, 0]
     * ```
     */
    "icon-translate"?: PropertyValueSpecification<[number, number]>,
    "icon-translate-transition"?: TransitionSpecification,
    /**
     * Controls the frame of reference for `icon-translate`.
     * 
     * @default
     * ```json
     * "map"
     * ```
     */
    "icon-translate-anchor"?: PropertyValueSpecification<"map" | "viewport">,
    /**
     * The opacity at which the text will be drawn.
     * 
     * @default
     * ```json
     * 1
     * ```
     */
    "text-opacity"?: DataDrivenPropertyValueSpecification<number>,
    "text-opacity-transition"?: TransitionSpecification,
    /**
     * The color with which the text will be drawn.
     * 
     * @default
     * ```json
     * "#000000"
     * ```
     */
    "text-color"?: DataDrivenPropertyValueSpecification<ColorSpecification>,
    "text-color-transition"?: TransitionSpecification,
    /**
     * The color of the text's halo, which helps it stand out from backgrounds.
     * 
     * @default
     * ```json
     * "rgba(0, 0, 0, 0)"
     * ```
     */
    "text-halo-color"?: DataDrivenPropertyValueSpecification<ColorSpecification>,
    "text-halo-color-transition"?: TransitionSpecification,
    /**
     * Distance of halo to the font outline. Max text halo width is 1/4 of the font-size.
     */
    "text-halo-width"?: DataDrivenPropertyValueSpecification<number>,
    "text-halo-width-transition"?: TransitionSpecification,
    /**
     * The halo's fadeout distance towards the outside.
     */
    "text-halo-blur"?: DataDrivenPropertyValueSpecification<number>,
    "text-halo-blur-transition"?: TransitionSpecification,
    /**
     * Distance that the text's anchor is moved from its original placement. Positive values indicate right and down, while negative values indicate left and up.
     * 
     * @default
     * ```json
     * [0, 0]
     * ```
     */
    "text-translate"?: PropertyValueSpecification<[number, number]>,
    "text-translate-transition"?: TransitionSpecification,
    /**
     * Controls the frame of reference for `text-translate`.
     * 
     * @default
     * ```json
     * "map"
     * ```
     */
    "text-translate-anchor"?: PropertyValueSpecification<"map" | "viewport">,
    /**
     * Circle radius.
     * 
     * @default
     * ```json
     * 5
     * ```
     */
    "circle-radius"?: DataDrivenPropertyValueSpecification<number>,
    "circle-radius-transition"?: TransitionSpecification,
    /**
     * The fill color of the circle.
     * 
     * @default
     * ```json
     * "#000000"
     * ```
     */
    "circle-color"?: DataDrivenPropertyValueSpecification<ColorSpecification>,
    "circle-color-transition"?: TransitionSpecification,
    /**
     * Amount to blur the circle. 1 blurs the circle such that only the centerpoint is full opacity.
     */
    "circle-blur"?: DataDrivenPropertyValueSpecification<number>,
    "circle-blur-transition"?: TransitionSpecification,
    /**
     * The opacity at which the circle will be drawn.
     * 
     * @default
     * ```json
     * 1
     * ```
     */
    "circle-opacity"?: DataDrivenPropertyValueSpecification<number>,
    "circle-opacity-transition"?: TransitionSpecification,
    /**
     * The geometry's offset. Values are `[x, y]` where negatives indicate left and up, respectively.
     * 
     * @default
     * ```json
     * [0, 0]
     * ```
     */
    "circle-translate"?: PropertyValueSpecification<[number, number]>,
    "circle-translate-transition"?: TransitionSpecification,
    /**
     * Controls the frame of reference for `circle-translate`.
     * 
     * @default
     * ```json
     * "map"
     * ```
     */
    "circle-translate-anchor"?: PropertyValueSpecification<"map" | "viewport">,
    /**
     * Controls the scaling behavior of the circle when the map is pitched.
     * 
     * @default
     * ```json
     * "map"
     * ```
     */
    "circle-pitch-scale"?: PropertyValueSpecification<"map" | "viewport">,
    /**
     * Orientation of circle when map is pitched.
     * 
     * @default
     * ```json
     * "viewport"
     * ```
     */
    "circle-pitch-alignment"?: PropertyValueSpecification<"map" | "viewport">,
    /**
     * The width of the circle's stroke. Strokes are placed outside of the `circle-radius`.
     */
    "circle-stroke-width"?: DataDrivenPropertyValueSpecification<number>,
    "circle-stroke-width-transition"?: TransitionSpecification,
    /**
     * The stroke color of the circle.
     * 
     * @default
     * ```json
     * "#000000"
     * ```
     */
    "circle-stroke-color"?: DataDrivenPropertyValueSpecification<ColorSpecification>,
    "circle-stroke-color-transition"?: TransitionSpecification,
    /**
     * The opacity of the circle's stroke.
     * 
     * @default
     * ```json
     * 1
     * ```
     */
    "circle-stroke-opacity"?: DataDrivenPropertyValueSpecification<number>,
    "circle-stroke-opacity-transition"?: TransitionSpecification,
    /**
     * Radius of influence of one heatmap point in pixels. Increasing the value makes the heatmap smoother, but less detailed.
     * 
     * @default
     * ```json
     * 30
     * ```
     */
    "heatmap-radius"?: DataDrivenPropertyValueSpecification<number>,
    "heatmap-radius-transition"?: TransitionSpecification,
    /**
     * A measure of how much an individual point contributes to the heatmap. A value of 10 would be equivalent to having 10 points of weight 1 in the same spot. Especially useful when combined with clustering.
     * 
     * @default
     * ```json
     * 1
     * ```
     */
    "heatmap-weight"?: DataDrivenPropertyValueSpecification<number>,
    /**
     * Similar to `heatmap-weight` but controls the intensity of the heatmap globally. Primarily used for adjusting the heatmap based on zoom level.
     * 
     * @default
     * ```json
     * 1
     * ```
     */
    "heatmap-intensity"?: PropertyValueSpecification<number>,
    "heatmap-intensity-transition"?: TransitionSpecification,
    /**
     * Defines the color of each pixel based on its density value in a heatmap.  Should be an expression that uses `["heatmap-density"]` as input.
     * 
     * @default
     * ```json
     * [
     *     "interpolate",
     *     ["linear"],
     *     ["heatmap-density"],
     *     0,
     *     "rgba(0, 0, 255, 0)",
     *     0.1,
     *     "royalblue",
     *     0.3,
     *     "cyan",
     *     0.5,
     *     "lime",
     *     0.7,
     *     "yellow",
     *     1,
     *     "red"
     * ]
     * ```
     */
    "heatmap-color"?: ExpressionSpecification,
    /**
     * The global opacity at which the heatmap layer will be drawn.
     * 
     * @default
     * ```json
     * 1
     * ```
     */
    "heatmap-opacity"?: PropertyValueSpecification<number>,
    "heatmap-opacity-transition"?: TransitionSpecification,
    /**
     * The opacity of the entire fill extrusion layer. This is rendered on a per-layer, not per-feature, basis, and data-driven styling is not available.
     * 
     * @default
     * ```json
     * 1
     * ```
     */
    "fill-extrusion-opacity"?: PropertyValueSpecification<number>,
    "fill-extrusion-opacity-transition"?: TransitionSpecification,
    /**
     * The base color of the extruded fill. The extrusion's surfaces will be shaded differently based on this color in combination with the root `light` settings. If this color is specified as `rgba` with an alpha component, the alpha component will be ignored; use `fill-extrusion-opacity` to set layer opacity.
     * 
     * @default
     * ```json
     * "#000000"
     * ```
     */
    "fill-extrusion-color"?: DataDrivenPropertyValueSpecification<ColorSpecification>,
    "fill-extrusion-color-transition"?: TransitionSpecification,
    /**
     * The geometry's offset. Values are `[x, y]` where negatives indicate left and up (on the flat plane), respectively.
     * 
     * @default
     * ```json
     * [0, 0]
     * ```
     */
    "fill-extrusion-translate"?: PropertyValueSpecification<[number, number]>,
    "fill-extrusion-translate-transition"?: TransitionSpecification,
    /**
     * Controls the frame of reference for `fill-extrusion-translate`.
     * 
     * @default
     * ```json
     * "map"
     * ```
     */
    "fill-extrusion-translate-anchor"?: PropertyValueSpecification<"map" | "viewport">,
    /**
     * Name of image in sprite to use for drawing images on extruded fills. For seamless patterns, image width and height must be a factor of two (2, 4, 8, ..., 512). Note that zoom-dependent expressions will be evaluated only at integer zoom levels.
     */
    "fill-extrusion-pattern"?: DataDrivenPropertyValueSpecification<ResolvedImageSpecification>,
    "fill-extrusion-pattern-transition"?: TransitionSpecification,
    /**
     * The height with which to extrude this layer. Negative values extrude below ground level, so a floor that is entirely underground can be expressed.
     */
    "fill-extrusion-height"?: DataDrivenPropertyValueSpecification<number>,
    "fill-extrusion-height-transition"?: TransitionSpecification,
    /**
     * The height with which to extrude the base of this layer. Must be less than or equal to `fill-extrusion-height`. Negative values extrude below ground level, e.g. underground floors.
     */
    "fill-extrusion-base"?: DataDrivenPropertyValueSpecification<number>,
    "fill-extrusion-base-transition"?: TransitionSpecification,
    /**
     * Whether to apply a vertical gradient to the sides of a fill-extrusion layer. If true, sides will be shaded slightly darker farther down.
     * 
     * @default
     * ```json
     * true
     * ```
     */
    "fill-extrusion-vertical-gradient"?: PropertyValueSpecification<boolean>,
    /**
     * The opacity at which the image will be drawn.
     * 
     * @default
     * ```json
     * 1
     * ```
     */
    "raster-opacity"?: PropertyValueSpecification<number>,
    "raster-opacity-transition"?: TransitionSpecification,
    /**
     * Rotates hues around the color wheel.
     */
    "raster-hue-rotate"?: PropertyValueSpecification<number>,
    "raster-hue-rotate-transition"?: TransitionSpecification,
    /**
     * Increase or reduce the brightness of the image. The value is the minimum brightness.
     */
    "raster-brightness-min"?: PropertyValueSpecification<number>,
    "raster-brightness-min-transition"?: TransitionSpecification,
    /**
     * Increase or reduce the brightness of the image. The value is the maximum brightness.
     * 
     * @default
     * ```json
     * 1
     * ```
     */
    "raster-brightness-max"?: PropertyValueSpecification<number>,
    "raster-brightness-max-transition"?: TransitionSpecification,
    /**
     * Increase or reduce the saturation of the image.
     */
    "raster-saturation"?: PropertyValueSpecification<number>,
    "raster-saturation-transition"?: TransitionSpecification,
    /**
     * Increase or reduce the contrast of the image.
     */
    "raster-contrast"?: PropertyValueSpecification<number>,
    "raster-contrast-transition"?: TransitionSpecification,
    /**
     * The resampling/interpolation method to use for overscaling, also known as texture magnification filter.
     * ![Visual comparison of linear resampling versus nearest resampling](assets/resampling.png)
     * 
     * @default
     * ```json
     * "linear"
     * ```
     */
    "resampling"?: PropertyValueSpecification<"linear" | "nearest">,
    /**
     * The resampling/interpolation method to use for overscaling, also known as texture magnification filter. It is advised to use the generic `resampling` paint property instead.
     * 
     * @default
     * ```json
     * "linear"
     * ```
     */
    "raster-resampling"?: PropertyValueSpecification<"linear" | "nearest">,
    /**
     * Fade duration when a new tile is added, or when a video is started or its coordinates are updated.
     * 
     * @default
     * ```json
     * 300
     * ```
     */
    "raster-fade-duration"?: PropertyValueSpecification<number>,
    /**
     * The direction of the light source(s) used to generate the hillshading with 0 as the top of the viewport if `hillshade-illumination-anchor` is set to `viewport` and due north if `hillshade-illumination-anchor` is set to `map`. Only when `hillshade-method` is set to `multidirectional` can you specify multiple light sources.
     * 
     * @default
     * ```json
     * 335
     * ```
     */
    "hillshade-illumination-direction"?: PropertyValueSpecification<NumberArraySpecification>,
    /**
     * The altitude of the light source(s) used to generate the hillshading with 0 as sunset and 90 as noon. Only when `hillshade-method` is set to `multidirectional` can you specify multiple light sources.
     * 
     * @default
     * ```json
     * 45
     * ```
     */
    "hillshade-illumination-altitude"?: PropertyValueSpecification<NumberArraySpecification>,
    /**
     * Direction of light source when map is rotated.
     * 
     * @default
     * ```json
     * "viewport"
     * ```
     */
    "hillshade-illumination-anchor"?: PropertyValueSpecification<"map" | "viewport">,
    /**
     * Intensity of the hillshade
     * 
     * @default
     * ```json
     * 0.5
     * ```
     */
    "hillshade-exaggeration"?: PropertyValueSpecification<number>,
    "hillshade-exaggeration-transition"?: TransitionSpecification,
    /**
     * The shading color of areas that face away from the light source(s). Only when `hillshade-method` is set to `multidirectional` can you specify multiple light sources.
     * 
     * @default
     * ```json
     * "#000000"
     * ```
     */
    "hillshade-shadow-color"?: PropertyValueSpecification<ColorArraySpecification>,
    "hillshade-shadow-color-transition"?: TransitionSpecification,
    /**
     * The shading color of areas that faces towards the light source(s). Only when `hillshade-method` is set to `multidirectional` can you specify multiple light sources.
     * 
     * @default
     * ```json
     * "#FFFFFF"
     * ```
     */
    "hillshade-highlight-color"?: PropertyValueSpecification<ColorArraySpecification>,
    "hillshade-highlight-color-transition"?: TransitionSpecification,
    /**
     * The shading color used to accentuate rugged terrain like sharp cliffs and gorges.
     * 
     * @default
     * ```json
     * "#000000"
     * ```
     */
    "hillshade-accent-color"?: PropertyValueSpecification<ColorSpecification>,
    "hillshade-accent-color-transition"?: TransitionSpecification,
    /**
     * The hillshade algorithm to use, one of `standard`, `basic`, `combined`, `igor`, or `multidirectional`.
     * ![Visual comparison of standard, basic, igor, combined, and multidirectional hillshade-method](assets/hillshade_methods.png)
     * 
     * @default
     * ```json
     * "standard"
     * ```
     */
    "hillshade-method"?: PropertyValueSpecification<"standard" | "basic" | "combined" | "igor" | "multidirectional">,
    /**
     * The opacity at which the color-relief will be drawn.
     * 
     * @default
     * ```json
     * 1
     * ```
     */
    "color-relief-opacity"?: PropertyValueSpecification<number>,
    "color-relief-opacity-transition"?: TransitionSpecification,
    /**
     * Defines the color of each pixel based on its elevation. Should be an expression that uses `["elevation"]` as input.
     * 
     * @example
     * ```json
     * [
     *     "interpolate",
     *     ["linear"],
     *     ["elevation"],
     *     0,
     *     "black",
     *     8849,
     *     "white"
     * ]
     * ```
     */
    "color-relief-color"?: ExpressionSpecification,
    /**
     * The color with which the background will be drawn.
     * 
     * @default
     * ```json
     * "#000000"
     * ```
     */
    "background-color"?: PropertyValueSpecification<ColorSpecification>,
    "background-color-transition"?: TransitionSpecification,
    /**
     * Name of image in sprite to use for drawing an image background. For seamless patterns, image width and height must be a factor of two (2, 4, 8, ..., 512). Note that zoom-dependent expressions will be evaluated only at integer zoom levels.
     */
    "background-pattern"?: PropertyValueSpecification<ResolvedImageSpecification>,
    "background-pattern-transition"?: TransitionSpecification,
    /**
     * The opacity at which the background will be drawn.
     * 
     * @default
     * ```json
     * 1
     * ```
     */
    "background-opacity"?: PropertyValueSpecification<number>,
    "background-opacity-transition"?: TransitionSpecification
};
/**
 * Union of all layout properties across all layer types.
 */
export type AllLayoutProperties = {
    /**
     * Sorts features in ascending order based on this value. Features with a higher sort key will appear above features with a lower sort key.
     */
    "fill-sort-key"?: DataDrivenPropertyValueSpecification<number>,
    /**
     * Whether this layer is displayed.
     * 
     * @default
     * ```json
     * "visible"
     * ```
     */
    "visibility"?: VisibilitySpecification,
    /**
     * The display of line endings.
     * 
     * @default
     * ```json
     * "butt"
     * ```
     */
    "line-cap"?: DataDrivenPropertyValueSpecification<"butt" | "round" | "square">,
    /**
     * The display of lines when joining.
     * 
     * @default
     * ```json
     * "miter"
     * ```
     */
    "line-join"?: DataDrivenPropertyValueSpecification<"bevel" | "round" | "miter">,
    /**
     * Used to automatically convert miter joins to bevel joins for sharp angles.
     * 
     * @default
     * ```json
     * 2
     * ```
     */
    "line-miter-limit"?: DataDrivenPropertyValueSpecification<number>,
    /**
     * Used to automatically convert round joins to miter joins for shallow angles.
     * 
     * @default
     * ```json
     * 1.05
     * ```
     */
    "line-round-limit"?: DataDrivenPropertyValueSpecification<number>,
    /**
     * Sorts features in ascending order based on this value. Features with a higher sort key will appear above features with a lower sort key.
     */
    "line-sort-key"?: DataDrivenPropertyValueSpecification<number>,
    /**
     * Label placement relative to its geometry.
     * 
     * @default
     * ```json
     * "point"
     * ```
     */
    "symbol-placement"?: PropertyValueSpecification<"point" | "line" | "line-center">,
    /**
     * Distance between two symbol anchors.
     * 
     * @default
     * ```json
     * 250
     * ```
     */
    "symbol-spacing"?: PropertyValueSpecification<number>,
    /**
     * If true, the symbols will not cross tile edges to avoid mutual collisions. Recommended in layers that don't have enough padding in the vector tile to prevent collisions, or if it is a point symbol layer placed after a line symbol layer. When using a client that supports global collision detection, like MapLibre GL JS version 0.42.0 or greater, enabling this property is not needed to prevent clipped labels at tile boundaries.
     */
    "symbol-avoid-edges"?: PropertyValueSpecification<boolean>,
    /**
     * Sorts features in ascending order based on this value. Features with lower sort keys are drawn and placed first.  When `icon-allow-overlap` or `text-allow-overlap` is `false`, features with a lower sort key will have priority during placement. When `icon-allow-overlap` or `text-allow-overlap` is set to `true`, features with a higher sort key will overlap over features with a lower sort key.
     */
    "symbol-sort-key"?: DataDrivenPropertyValueSpecification<number>,
    /**
     * Determines whether overlapping symbols in the same layer are rendered in the order that they appear in the data source or by their y-position relative to the viewport. To control the order and prioritization of symbols otherwise, use `symbol-sort-key`.
     * 
     * @default
     * ```json
     * "auto"
     * ```
     */
    "symbol-z-order"?: PropertyValueSpecification<"auto" | "viewport-y" | "source">,
    /**
     * If true, the icon will be visible even if it collides with other previously drawn symbols.
     */
    "icon-allow-overlap"?: PropertyValueSpecification<boolean>,
    /**
     * Allows for control over whether to show an icon when it overlaps other symbols on the map. If `icon-overlap` is not set, `icon-allow-overlap` is used instead.
     */
    "icon-overlap"?: PropertyValueSpecification<"never" | "always" | "cooperative">,
    /**
     * If true, other symbols can be visible even if they collide with the icon.
     */
    "icon-ignore-placement"?: PropertyValueSpecification<boolean>,
    /**
     * If true, text will display without their corresponding icons when the icon collides with other symbols and the text does not.
     */
    "icon-optional"?: PropertyValueSpecification<boolean>,
    /**
     * In combination with `symbol-placement`, determines the rotation behavior of icons.
     * 
     * @default
     * ```json
     * "auto"
     * ```
     */
    "icon-rotation-alignment"?: DataDrivenPropertyValueSpecification<"map" | "viewport" | "auto">,
    /**
     * Scales the original size of the icon by the provided factor. The new pixel size of the image will be the original pixel size multiplied by `icon-size`. 1 is the original size; 3 triples the size of the image.
     * 
     * @default
     * ```json
     * 1
     * ```
     */
    "icon-size"?: DataDrivenPropertyValueSpecification<number>,
    /**
     * Scales the icon to fit around the associated text.
     * 
     * @default
     * ```json
     * "none"
     * ```
     */
    "icon-text-fit"?: PropertyValueSpecification<"none" | "width" | "height" | "both">,
    /**
     * Size of the additional area added to dimensions determined by `icon-text-fit`, in clockwise order: top, right, bottom, left.
     * 
     * @default
     * ```json
     * [0, 0, 0, 0]
     * ```
     */
    "icon-text-fit-padding"?: PropertyValueSpecification<[number, number, number, number]>,
    /**
     * Name of image in sprite to use for drawing an image background.
     */
    "icon-image"?: DataDrivenPropertyValueSpecification<ResolvedImageSpecification>,
    /**
     * Rotates the icon clockwise.
     */
    "icon-rotate"?: DataDrivenPropertyValueSpecification<number>,
    /**
     * Size of additional area round the icon bounding box used for detecting symbol collisions.
     * 
     * @default
     * ```json
     * [2]
     * ```
     */
    "icon-padding"?: DataDrivenPropertyValueSpecification<PaddingSpecification>,
    /**
     * If true, the icon may be flipped to prevent it from being rendered upside-down.
     */
    "icon-keep-upright"?: PropertyValueSpecification<boolean>,
    /**
     * Offset distance of icon from its anchor. Positive values indicate right and down, while negative values indicate left and up. Each component is multiplied by the value of `icon-size` to obtain the final offset in pixels. When combined with `icon-rotate` the offset will be as if the rotated direction was up.
     * 
     * @default
     * ```json
     * [0, 0]
     * ```
     */
    "icon-offset"?: DataDrivenPropertyValueSpecification<[number, number]>,
    /**
     * Part of the icon placed closest to the anchor.
     * 
     * @default
     * ```json
     * "center"
     * ```
     */
    "icon-anchor"?: DataDrivenPropertyValueSpecification<"center" | "left" | "right" | "top" | "bottom" | "top-left" | "top-right" | "bottom-left" | "bottom-right">,
    /**
     * Orientation of icon when map is pitched.
     * 
     * @default
     * ```json
     * "auto"
     * ```
     */
    "icon-pitch-alignment"?: PropertyValueSpecification<"map" | "viewport" | "auto">,
    /**
     * Orientation of text when map is pitched.
     * 
     * @default
     * ```json
     * "auto"
     * ```
     */
    "text-pitch-alignment"?: PropertyValueSpecification<"map" | "viewport" | "auto">,
    /**
     * In combination with `symbol-placement`, determines the rotation behavior of the individual glyphs forming the text.
     * 
     * @default
     * ```json
     * "auto"
     * ```
     */
    "text-rotation-alignment"?: PropertyValueSpecification<"map" | "viewport" | "viewport-glyph" | "auto">,
    /**
     * Value to use for a text label. If a plain `string` is provided, it will be treated as a `formatted` with default/inherited formatting options.
     */
    "text-field"?: DataDrivenPropertyValueSpecification<FormattedSpecification>,
    /**
     * Fonts to use for displaying text. If the `glyphs` root property is specified, this array is joined together and interpreted as a font stack name. Otherwise, it is interpreted as a cascading fallback list of local font names.
     * 
     * @default
     * ```json
     * ["Open Sans Regular", "Arial Unicode MS Regular"]
     * ```
     */
    "text-font"?: DataDrivenPropertyValueSpecification<Array<string>>,
    /**
     * Font size.
     * 
     * @default
     * ```json
     * 16
     * ```
     */
    "text-size"?: DataDrivenPropertyValueSpecification<number>,
    /**
     * The maximum line width for text wrapping.
     * 
     * @default
     * ```json
     * 10
     * ```
     */
    "text-max-width"?: DataDrivenPropertyValueSpecification<number>,
    /**
     * Text leading value for multi-line text.
     * 
     * @default
     * ```json
     * 1.2
     * ```
     */
    "text-line-height"?: PropertyValueSpecification<number>,
    /**
     * Text tracking amount.
     */
    "text-letter-spacing"?: DataDrivenPropertyValueSpecification<number>,
    /**
     * Text justification options.
     * 
     * @default
     * ```json
     * "center"
     * ```
     */
    "text-justify"?: DataDrivenPropertyValueSpecification<"auto" | "left" | "center" | "right">,
    /**
     * Radial offset of text, in the direction of the symbol's anchor. Useful in combination with `text-variable-anchor`, which defaults to using the two-dimensional `text-offset` if present.
     */
    "text-radial-offset"?: DataDrivenPropertyValueSpecification<number>,
    /**
     * To increase the chance of placing high-priority labels on the map, you can provide an array of `text-anchor` locations: the renderer will attempt to place the label at each location, in order, before moving onto the next label. Use `text-justify: auto` to choose justification based on anchor position. To apply an offset, use the `text-radial-offset` or the two-dimensional `text-offset`.
     * 
     * @example
     * ```json
     * ["center", "left", "right"]
     * ```
     */
    "text-variable-anchor"?: PropertyValueSpecification<Array<"center" | "left" | "right" | "top" | "bottom" | "top-left" | "top-right" | "bottom-left" | "bottom-right">>,
    /**
     * To increase the chance of placing high-priority labels on the map, you can provide an array of `text-anchor` locations, each paired with an offset value. The renderer will attempt to place the label at each location, in order, before moving on to the next location+offset. Use `text-justify: auto` to choose justification based on anchor position. 
     * 
     *  The length of the array must be even, and must alternate between enum and point entries. i.e., each anchor location must be accompanied by a point, and that point defines the offset when the corresponding anchor location is used. Positive offset values indicate right and down, while negative values indicate left and up. Anchor locations may repeat, allowing the renderer to try multiple offsets to try and place a label using the same anchor. 
     * 
     *  When present, this property takes precedence over `text-anchor`, `text-variable-anchor`, `text-offset`, and `text-radial-offset`. 
     * 
     *  ```json 
     * 
     *  { "text-variable-anchor-offset": ["top", [0, 4], "left", [3,0], "bottom", [1, 1]] } 
     * 
     *  ``` 
     * 
     *  When the renderer chooses the `top` anchor, `[0, 4]` will be used for `text-offset`; the text will be shifted down by 4 ems. 
     * 
     *  When the renderer chooses the `left` anchor, `[3, 0]` will be used for `text-offset`; the text will be shifted right by 3 ems.
     * 
     * @example
     * ```json
     * ["top", [0, 4], "left", [3, 0], "bottom", [1, 1]]
     * ```
     */
    "text-variable-anchor-offset"?: DataDrivenPropertyValueSpecification<VariableAnchorOffsetCollectionSpecification>,
    /**
     * Part of the text placed closest to the anchor.
     * 
     * @default
     * ```json
     * "center"
     * ```
     */
    "text-anchor"?: DataDrivenPropertyValueSpecification<"center" | "left" | "right" | "top" | "bottom" | "top-left" | "top-right" | "bottom-left" | "bottom-right">,
    /**
     * Maximum angle change between adjacent characters.
     * 
     * @default
     * ```json
     * 45
     * ```
     */
    "text-max-angle"?: PropertyValueSpecification<number>,
    /**
     * The property allows control over a symbol's orientation. Note that the property values act as a hint, so that a symbol whose language doesn’t support the provided orientation will be laid out in its natural orientation. Example: English point symbol will be rendered horizontally even if array value contains single 'vertical' enum value. The order of elements in an array define priority order for the placement of an orientation variant.
     */
    "text-writing-mode"?: PropertyValueSpecification<Array<"horizontal" | "vertical">>,
    /**
     * Rotates the text clockwise.
     */
    "text-rotate"?: DataDrivenPropertyValueSpecification<number>,
    /**
     * Size of the additional area around the text bounding box used for detecting symbol collisions.
     * 
     * @default
     * ```json
     * 2
     * ```
     */
    "text-padding"?: PropertyValueSpecification<number>,
    /**
     * If true, the text may be flipped vertically to prevent it from being rendered upside-down.
     * 
     * @default
     * ```json
     * true
     * ```
     */
    "text-keep-upright"?: PropertyValueSpecification<boolean>,
    /**
     * Specifies how to capitalize text, similar to the CSS `text-transform` property.
     * 
     * @default
     * ```json
     * "none"
     * ```
     */
    "text-transform"?: DataDrivenPropertyValueSpecification<"none" | "uppercase" | "lowercase">,
    /**
     * Offset distance of text from its anchor. Positive values indicate right and down, while negative values indicate left and up. If used with text-variable-anchor, input values will be taken as absolute values. Offsets along the x- and y-axis will be applied automatically based on the anchor position.
     * 
     * @default
     * ```json
     * [0, 0]
     * ```
     */
    "text-offset"?: DataDrivenPropertyValueSpecification<[number, number]>,
    /**
     * If true, the text will be visible even if it collides with other previously drawn symbols.
     */
    "text-allow-overlap"?: PropertyValueSpecification<boolean>,
    /**
     * Allows for control over whether to show symbol text when it overlaps other symbols on the map. If `text-overlap` is not set, `text-allow-overlap` is used instead
     */
    "text-overlap"?: PropertyValueSpecification<"never" | "always" | "cooperative">,
    /**
     * If true, other symbols can be visible even if they collide with the text.
     */
    "text-ignore-placement"?: PropertyValueSpecification<boolean>,
    /**
     * If true, icons will display without their corresponding text when the text collides with other symbols and the icon does not.
     */
    "text-optional"?: PropertyValueSpecification<boolean>,
    /**
     * The height above the anchor, in meters, at which the symbol is placed. Use `symbol-height-anchor` to control what this height is measured from.
     */
    "symbol-height-offset"?: DataDrivenPropertyValueSpecification<number>,
    /**
     * Defines what `symbol-height-offset` is measured from.
     * 
     * @default
     * ```json
     * "ground"
     * ```
     */
    "symbol-height-anchor"?: PropertyValueSpecification<"ground" | "absolute">,
    /**
     * Sorts features in ascending order based on this value. Features with a higher sort key will appear above features with a lower sort key.
     */
    "circle-sort-key"?: DataDrivenPropertyValueSpecification<number>,
    /**
     * The distance from each fill extrusion corner, measured along the adjacent edges, that is replaced by a rounded corner. A value of `0` disables rounded corners.
     */
    "fill-extrusion-rounded-corner-distance"?: number
};
